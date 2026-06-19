"""Couche d'appel LLM construite sur le client AsyncOpenAI.

Deux points d'entrée publics :
- ``call_llm``            — réponse texte brut, mode thinking optionnel
- ``call_llm_structured`` — sortie structurée (modèle Pydantic), sans thinking

Helpers partagés déplacés dans ``utils.utils`` :
- Sanitization / nettoyage des entrées → ``sanitize_text``
- Estimation de tokens              → ``estimate_tokens``
- Modèle de message                 → ``LLMMessage``
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, TypeVar

from pydantic import BaseModel, Field

from core.config import (
    LLM_COMPACT_RECENT_KEEP,
    LLM_COMPACT_THRESHOLD_RATIO,
    LLM_CONTEXT_WINDOW_TOKENS,
    LLM_MAX_CONCURRENT,
    LLM_MODEL,
    LLM_TIMEOUT_SECONDS,
)
from core.llm_client import build_llm_client
from utils.utils import LLMMessage, estimate_tokens  # noqa: F401 — re-exported

# ---------------------------------------------------------------------------
# Client partagé (singleton)
# ---------------------------------------------------------------------------

_client = build_llm_client()
_logger = logging.getLogger(__name__)

# Le sémaphore évite de saturer le serveur LLM avec des requêtes concurrentes.
_semaphore = asyncio.Semaphore(LLM_MAX_CONCURRENT)

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# Schémas Pydantic pour les appels LLM
# ---------------------------------------------------------------------------


class LLMRequest(BaseModel):
    """Paramètres d'un appel LLM texte brut."""

    system_prompt: str = Field(min_length=1)
    messages: list[LLMMessage] = Field(min_length=1)
    model: str = Field(default=LLM_MODEL)
    temperature: float = Field(default=0.4, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, gt=0, le=32768)
    thinking: bool = Field(default=False)


class LLMResponse(BaseModel):
    """Résultat d'un appel LLM texte brut."""

    content: str
    model: str
    input_tokens: int
    output_tokens: int


class LLMStructuredRequest(BaseModel):
    """Paramètres d'un appel LLM à sortie structurée."""

    system_prompt: str = Field(min_length=1)
    messages: list[LLMMessage] = Field(min_length=1)
    model: str = Field(default=LLM_MODEL)
    temperature: float = Field(default=0.4, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, gt=0, le=32768)
    timeout: float | None = Field(
        default=None, gt=0, description="Override LLM_TIMEOUT_SECONDS pour cet appel."
    )


# ---------------------------------------------------------------------------
# Helper interne
# ---------------------------------------------------------------------------


def _build_openai_messages(
    system_prompt: str, messages: list[LLMMessage]
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    result.extend({"role": m.role, "content": m.content} for m in messages)
    return result


# ---------------------------------------------------------------------------
# Points d'entrée publics
# ---------------------------------------------------------------------------


async def call_llm(request: LLMRequest) -> LLMResponse:
    """Envoie une requête chat completion texte brut au LLM.

    Supporte le mode thinking via ``extra_body`` (compatible vLLM).
    Thinking et sortie structurée sont mutuellement exclusifs.

    Raises:
        TimeoutError: si le LLM dépasse ``LLM_TIMEOUT_SECONDS``.
        APIStatusError: sur des réponses 4xx/5xx du provider.
        APIConnectionError: sur des erreurs réseau.
    """
    messages = _build_openai_messages(request.system_prompt, request.messages)

    extra_body: dict[str, Any] = {}
    if not request.thinking:
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
    """Envoie une requête à sortie structurée et valide contre ``schema``.

    Le mode thinking est intentionnellement désactivé — incompatible avec
    le schéma JSON strict.

    Raises:
        TimeoutError: si le LLM dépasse ``LLM_TIMEOUT_SECONDS``.
        APIStatusError: sur des réponses 4xx/5xx du provider.
        ValidationError: si la réponse ne correspond pas à ``schema``.
    """
    messages = _build_openai_messages(request.system_prompt, request.messages)
    extra_body: dict[str, Any] = {"chat_template_kwargs": {"enable_thinking": False}}

    effective_timeout = (
        request.timeout if request.timeout is not None else LLM_TIMEOUT_SECONDS
    )
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
            timeout=effective_timeout,
        )

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("LLM returned an empty structured response")

    return parsed


# ---------------------------------------------------------------------------
# Gestion de la fenêtre de contexte
# ---------------------------------------------------------------------------


class ContextWindowInfo(BaseModel):
    """Instantané de l'utilisation de la fenêtre de contexte — renvoyé au frontend."""

    used_tokens: int
    limit_tokens: int
    usage_ratio: float  # 0.0 – 1.0
    was_compacted: bool


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
    """Résume les anciens messages quand l'historique approche la limite.

    Conserve les ``LLM_COMPACT_RECENT_KEEP`` messages récents verbatim et
    remplace le reste par un résumé condensé produit par le LLM.

    Args:
        messages: Liste ordonnée de messages (plus ancien en premier).

    Returns:
        (messages_compactés, context_info)
    """
    from core.prompts import COMPACTION_PROMPT  # évite l'import circulaire

    compact_threshold = int(LLM_CONTEXT_WINDOW_TOKENS * LLM_COMPACT_THRESHOLD_RATIO)
    current_tokens = _estimate_history_tokens(messages)

    if current_tokens <= compact_threshold or len(messages) <= LLM_COMPACT_RECENT_KEEP:
        return messages, _build_context_info(messages, was_compacted=False)

    to_summarize = messages[:-LLM_COMPACT_RECENT_KEEP]
    recent = messages[-LLM_COMPACT_RECENT_KEEP:]

    history_text = "\n".join(f"{m.role.upper()}: {m.content}" for m in to_summarize)

    try:
        summary_response = await call_llm(
            LLMRequest(
                system_prompt=COMPACTION_PROMPT,
                messages=[LLMMessage(role="user", content=history_text)],
                temperature=0.3,
                max_tokens=512,
            )
        )
    except Exception:
        # En cas d'échec LLM, on retourne l'historique non compacté plutôt que de bloquer la requête.
        _logger.warning(
            "[llm] compact_history_if_needed: LLM error, returning uncompacted history"
        )
        return messages, _build_context_info(messages, was_compacted=False)

    summary_message = LLMMessage(
        role="assistant",
        content=f"[Résumé du contexte précédent]\n{summary_response.content}",
    )

    compacted = [summary_message, *recent]
    return compacted, _build_context_info(compacted, was_compacted=True)
