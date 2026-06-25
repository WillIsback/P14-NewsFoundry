"""Instrumentation des latences d'inférence LLM.

`InferenceTrace` est propagé via `contextvars.ContextVar` — isolation automatique
entre coroutines asyncio concurrentes. Les fonctions record_* sont des no-ops si
aucune trace n'est active dans le contexte courant.
"""

from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Generator, Literal

from opentelemetry import trace as otel_trace

_logger = logging.getLogger(__name__)

_tracer = otel_trace.get_tracer("newsfoundry")

_active_trace: ContextVar[InferenceTrace | None] = ContextVar(
    "_active_trace", default=None
)


@dataclass
class _LLMRecord:
    input_tokens: int
    output_tokens: int
    duration_s: float
    model: str


@dataclass
class _ToolRecord:
    tool_name: str
    duration_s: float


@dataclass
class InferenceTrace:
    operation: Literal["chat_turn", "press_review"]
    _started_at: float = field(default_factory=time.perf_counter)
    _llm_records: list[_LLMRecord] = field(default_factory=list)
    _tool_records: list[_ToolRecord] = field(default_factory=list)
    _was_compacted: bool = False
    _history_length: int = 0

    @classmethod
    def start(cls, operation: Literal["chat_turn", "press_review"]) -> "InferenceTrace":
        trace = cls(operation=operation)
        _active_trace.set(trace)
        return trace

    def record_llm(
        self,
        *,
        input_tokens: int,
        output_tokens: int,
        duration_s: float,
        model: str,
    ) -> None:
        self._llm_records.append(
            _LLMRecord(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_s=duration_s,
                model=model,
            )
        )
        tok_per_sec = round(output_tokens / duration_s, 1) if duration_s > 0 else 0.0
        _logger.info(
            "[observability] llm_call duration_s=%.3f input=%d output=%d tok/s=%.1f model=%s",
            duration_s,
            input_tokens,
            output_tokens,
            tok_per_sec,
            model,
        )

    def record_tool(self, *, tool_name: str, duration_s: float) -> None:
        self._tool_records.append(
            _ToolRecord(tool_name=tool_name, duration_s=duration_s)
        )
        _logger.info(
            "[observability] tool_call tool=%s duration_s=%.3f", tool_name, duration_s
        )

    def record_compaction(self, *, was_compacted: bool, history_length: int) -> None:
        self._was_compacted = was_compacted
        self._history_length = history_length

    def flush(self, *, chat_id: int, articles_count: int = 0) -> None:
        e2e = time.perf_counter() - self._started_at
        input_tokens_total = sum(r.input_tokens for r in self._llm_records)
        output_tokens_total = sum(r.output_tokens for r in self._llm_records)
        llm_duration_total = sum(r.duration_s for r in self._llm_records)
        tok_per_sec = (
            round(output_tokens_total / llm_duration_total, 1)
            if llm_duration_total > 0
            else 0.0
        )
        tool_latency = sum(r.duration_s for r in self._tool_records)

        if self.operation == "chat_turn":
            _logger.info(
                "[observability] chat_turn_complete chat_id=%d e2e=%.3fs "
                "llm_calls=%d tokens_in=%d tokens_out=%d tok/s=%.1f "
                "tools=%d tool_latency=%.3fs compacted=%s history=%d",
                chat_id,
                e2e,
                len(self._llm_records),
                input_tokens_total,
                output_tokens_total,
                tok_per_sec,
                len(self._tool_records),
                tool_latency,
                self._was_compacted,
                self._history_length,
            )
        else:
            _logger.info(
                "[observability] press_review_complete chat_id=%d e2e=%.3fs "
                "tokens_in=%d tokens_out=%d tok/s=%.1f articles=%d",
                chat_id,
                e2e,
                input_tokens_total,
                output_tokens_total,
                tok_per_sec,
                articles_count,
            )


@contextmanager
def rag_span(query: str, top_k: int) -> Generator[otel_trace.Span, None, None]:
    """Context manager — span OpenInference RETRIEVER autour du RAG.

    Yielde le span pour permettre l'ajout d'attributs dynamiques
    (documents récupérés, retrieved_count) depuis le code appelant.

    Usage:
        with rag_span(query=query, top_k=5) as span:
            results = build_index_and_retrieve(articles, query, top_k=5)
            for i, a in enumerate(results):
                span.set_attribute(f"retrieval.documents.{i}.document.content", a["summary"])
            span.set_attribute("rag.retrieved_count", len(results))
    """
    with _tracer.start_as_current_span("rag_retrieve") as span:
        span.set_attribute("openinference.span.kind", "RETRIEVER")
        span.set_attribute("input.value", query)
        span.set_attribute("rag.top_k", top_k)
        yield span


@contextmanager
def press_review_span(articles: list[dict]) -> Generator[otel_trace.Span, None, None]:
    """Context manager — span OpenInference CHAIN autour de la génération de revue de presse.

    Yielde le span pour permettre l'ajout de l'output après la génération.

    Usage:
        with press_review_span(articles=all_articles) as span:
            result = await Runner.run(agent, input=messages)
            if result.final_output:
                span.set_attribute("output.value", result.final_output.title + " — " + result.final_output.editorial[:200])
                span.set_attribute("chat.articles_count", len(all_articles))
    """
    with _tracer.start_as_current_span("press_review_generation") as span:
        span.set_attribute("openinference.span.kind", "CHAIN")
        sources = [
            {"title": a.get("title", ""), "url": a.get("url", "")} for a in articles
        ]
        span.set_attribute("input.value", json.dumps(sources, ensure_ascii=False))
        yield span


def get_active_trace() -> InferenceTrace | None:
    """Retourne la trace active dans le contexte asyncio courant, ou None."""
    return _active_trace.get()


@contextmanager
def tracing_context(session_id: str) -> Generator[None, None, None]:
    """Context manager MLflow Tracing — no-op si MLFLOW_TRACKING_URI absent."""
    from core.config import MLFLOW_TRACKING_URI

    if not MLFLOW_TRACKING_URI:
        yield
        return

    import mlflow

    with mlflow.tracing.context(session_id=session_id):
        yield
