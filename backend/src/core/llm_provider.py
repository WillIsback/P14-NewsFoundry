"""Generic LLM call layer built on the AsyncOpenAI client.

Provides two entry points:
- ``call_llm``            — plain text response, optional thinking mode
- ``call_llm_structured`` — structured output (Pydantic model), no thinking

Both entry points share:
- Input sanitisation (length cap, control-char strip)
- Asyncio semaphore for max-concurrency control
- Per-call timeout via asyncio.wait_for
- Typed request / response Pydantic models
"""

from __future__ import annotations

import asyncio
import re
import unicodedata
from typing import Any, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, field_validator

from core.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_COMPACT_RECENT_KEEP,
    LLM_COMPACT_THRESHOLD_RATIO,
    LLM_CONTEXT_WINDOW_TOKENS,
    LLM_MAX_CONCURRENT,
    LLM_MAX_INPUT_CHARS,
    LLM_MODEL,
    LLM_TIMEOUT_SECONDS,
)

# ---------------------------------------------------------------------------
# Shared client (singleton)
# ---------------------------------------------------------------------------

_client = AsyncOpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
)

# Semaphore prevents saturating the LLM server with concurrent requests.
_semaphore = asyncio.Semaphore(LLM_MAX_CONCURRENT)

T = TypeVar("T", bound=BaseModel)

# ---------------------------------------------------------------------------
# Control characters to strip (everything below U+0020 except tab/newline)
# ---------------------------------------------------------------------------
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


# ---------------------------------------------------------------------------
# Pydantic schemas for call inputs
# ---------------------------------------------------------------------------


class LLMMessage(BaseModel):
    """A single chat message."""

    role: str = Field(pattern=r"^(system|user|assistant)$")
    content: str = Field(min_length=1)

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        # Strip dangerous control characters (prompt injection vector)
        v = _CONTROL_CHAR_RE.sub("", v)
        # Normalize unicode to NFC to prevent homoglyph attacks
        v = unicodedata.normalize("NFC", v)
        if len(v) > LLM_MAX_INPUT_CHARS:
            raise ValueError(
                f"Message content exceeds maximum length of {LLM_MAX_INPUT_CHARS} characters"
            )
        return v


class LLMRequest(BaseModel):
    """Input schema for a plain-text LLM call."""

    system_prompt: str = Field(min_length=1)
    messages: list[LLMMessage] = Field(min_length=1)
    model: str = Field(default=LLM_MODEL)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, gt=0, le=32768)
    thinking: bool = Field(default=False)


class LLMResponse(BaseModel):
    """Output schema for a plain-text LLM call."""

    content: str
    model: str
    input_tokens: int
    output_tokens: int


class LLMStructuredRequest(BaseModel):
    """Input schema for a structured-output LLM call."""

    system_prompt: str = Field(min_length=1)
    messages: list[LLMMessage] = Field(min_length=1)
    model: str = Field(default=LLM_MODEL)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, gt=0, le=32768)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_openai_messages(
    system_prompt: str, messages: list[LLMMessage]
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    result.extend({"role": m.role, "content": m.content} for m in messages)
    return result


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


async def call_llm(request: LLMRequest) -> LLMResponse:
    """Send a plain-text chat completion request to the LLM.

    Supports optional thinking mode via ``extra_body`` (vLLM-compatible).
    Thinking mode and structured output are mutually exclusive — use
    ``call_llm_structured`` for JSON schema enforcement.

    Raises:
        TimeoutError: if the LLM takes longer than ``LLM_TIMEOUT_SECONDS``.
        APIStatusError: on 4xx/5xx responses from the provider.
        APIConnectionError: on network-level failures.
    """
    messages = _build_openai_messages(request.system_prompt, request.messages)

    extra_body: dict[str, Any] = {}
    if request.thinking:
        extra_body["chat_template_kwargs"] = {"enable_thinking": False}

    async with _semaphore:
        completion = await asyncio.wait_for(
            _client.chat.completions.create(
                model=request.model,
                messages=messages,  # type: ignore[arg-type]
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                extra_body=extra_body or None,
            ),
            timeout=LLM_TIMEOUT_SECONDS,
        )

    choice = completion.choices[0]
    usage = completion.usage

    return LLMResponse(
        content=choice.message.content or "",
        model=completion.model,
        input_tokens=usage.prompt_tokens if usage else 0,
        output_tokens=usage.completion_tokens if usage else 0,
    )


async def call_llm_structured(request: LLMStructuredRequest, schema: type[T]) -> T:
    """Send a structured-output chat completion request to the LLM.

    The response is parsed and validated against ``schema`` (a Pydantic model).
    Thinking mode is intentionally disabled here — the two features are
    incompatible (free-form reasoning vs. strict JSON schema).

    Raises:
        TimeoutError: if the LLM takes longer than ``LLM_TIMEOUT_SECONDS``.
        APIStatusError: on 4xx/5xx responses from the provider.
        APIConnectionError: on network-level failures.
        ValidationError: if the response does not match ``schema``.
    """
    messages = _build_openai_messages(request.system_prompt, request.messages)

    # Thinking mode is intentionally disabled for structured output — the two
    # features are incompatible (free-form reasoning vs. strict JSON schema).
    extra_body: dict[str, Any] = {"chat_template_kwargs": {"enable_thinking": False}}

    async with _semaphore:
        completion = await asyncio.wait_for(
            _client.beta.chat.completions.parse(
                model=request.model,
                messages=messages,  # type: ignore[arg-type]
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                response_format=schema,
                extra_body=extra_body,
            ),
            timeout=LLM_TIMEOUT_SECONDS,
        )

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("LLM returned an empty structured response")

    return parsed


# ---------------------------------------------------------------------------
# Context window management
# ---------------------------------------------------------------------------


class ContextWindowInfo(BaseModel):
    """Snapshot of context window usage — returned to the frontend."""

    used_tokens: int
    limit_tokens: int
    usage_ratio: float  # 0.0 – 1.0
    was_compacted: bool


def estimate_tokens(text: str) -> int:
    """Rough token count: ~4 characters per token (GPT-family heuristic)."""
    return max(1, len(text) // 4)


def _estimate_history_tokens(messages: list[LLMMessage]) -> int:
    return sum(estimate_tokens(m.content) for m in messages)


def _build_context_info(
    messages: list[LLMMessage], was_compacted: bool
) -> ContextWindowInfo:
    used = _estimate_history_tokens(messages)
    return ContextWindowInfo(
        used_tokens=used,
        limit_tokens=LLM_CONTEXT_WINDOW_TOKENS,
        usage_ratio=round(used / LLM_CONTEXT_WINDOW_TOKENS, 4),
        was_compacted=was_compacted,
    )


async def compact_history_if_needed(
    messages: list[LLMMessage],
) -> tuple[list[LLMMessage], ContextWindowInfo]:
    """Summarize old messages when the history approaches the context limit.

    Keeps the ``LLM_COMPACT_RECENT_KEEP`` most recent messages verbatim and
    replaces everything before them with a single condensed summary produced
    by the LLM. The current session is preserved — nothing is deleted from
    the database.

    This function must be called **before** ``call_llm``, not inside it, to
    avoid nested semaphore acquisition.

    Args:
        messages: Ordered list of conversation messages (oldest first).

    Returns:
        (compacted_messages, context_info) where ``context_info`` carries
        the token usage snapshot and the ``was_compacted`` flag for the
        frontend.
    """
    # Import here to avoid circular import (prompts → llm_provider)
    from core.prompts import COMPACTION_PROMPT

    compact_threshold = int(LLM_CONTEXT_WINDOW_TOKENS * LLM_COMPACT_THRESHOLD_RATIO)
    current_tokens = _estimate_history_tokens(messages)

    if current_tokens <= compact_threshold or len(messages) <= LLM_COMPACT_RECENT_KEEP:
        return messages, _build_context_info(messages, was_compacted=False)

    to_summarize = messages[:-LLM_COMPACT_RECENT_KEEP]
    recent = messages[-LLM_COMPACT_RECENT_KEEP:]

    history_text = "\n".join(f"{m.role.upper()}: {m.content}" for m in to_summarize)

    summary_response = await call_llm(
        LLMRequest(
            system_prompt=COMPACTION_PROMPT,
            messages=[LLMMessage(role="user", content=history_text)],
            temperature=0.3,
            max_tokens=512,
        )
    )

    summary_message = LLMMessage(
        role="assistant",
        content=f"[Résumé du contexte précédent]\n{summary_response.content}",
    )

    compacted = [summary_message, *recent]
    return compacted, _build_context_info(compacted, was_compacted=True)
