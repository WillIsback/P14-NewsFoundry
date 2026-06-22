"""Tests de InferenceTrace — logs structurés et isolation de contexte."""

import asyncio
import pytest

from core.observability import InferenceTrace, get_active_trace
import core.observability as _obs_module


@pytest.fixture(autouse=True)
def reset_active_trace():
    """Réinitialise le ContextVar entre les tests pour éviter la pollution."""
    token = _obs_module._active_trace.set(None)
    yield
    _obs_module._active_trace.reset(token)


def test_get_active_trace_returns_none_by_default():
    assert get_active_trace() is None


def test_start_sets_active_trace():
    trace = InferenceTrace.start("chat_turn")
    assert get_active_trace() is trace


def test_record_llm_accumulates():
    trace = InferenceTrace.start("chat_turn")
    trace.record_llm(input_tokens=100, output_tokens=50, duration_s=1.0, model="qwen3")
    trace.record_llm(input_tokens=200, output_tokens=80, duration_s=2.0, model="qwen3")
    assert len(trace._llm_records) == 2
    assert trace._llm_records[0].input_tokens == 100
    assert trace._llm_records[1].output_tokens == 80


def test_record_tool_accumulates():
    trace = InferenceTrace.start("chat_turn")
    trace.record_tool(tool_name="get_top_news", duration_s=3.1)
    assert len(trace._tool_records) == 1
    assert trace._tool_records[0].tool_name == "get_top_news"


def test_record_compaction_stores_state():
    trace = InferenceTrace.start("chat_turn")
    trace.record_compaction(was_compacted=True, history_length=42)
    assert trace._was_compacted is True
    assert trace._history_length == 42


def test_flush_chat_turn_emits_log(caplog):
    """flush() émet un log structuré chat_turn_complete."""
    import logging

    trace = InferenceTrace.start("chat_turn")
    trace.record_llm(input_tokens=100, output_tokens=50, duration_s=1.0, model="qwen3")
    trace.record_tool(tool_name="get_top_news", duration_s=0.5)
    with caplog.at_level(logging.INFO, logger="core.observability"):
        trace.flush(chat_id=1)
    assert any("chat_turn_complete" in r.message for r in caplog.records)


def test_flush_press_review_emits_log(caplog):
    """flush() émet un log structuré press_review_complete."""
    import logging

    trace = InferenceTrace.start("press_review")
    trace.record_llm(input_tokens=800, output_tokens=400, duration_s=5.0, model="qwen3")
    with caplog.at_level(logging.INFO, logger="core.observability"):
        trace.flush(chat_id=2, articles_count=3)
    assert any("press_review_complete" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_context_isolation_between_coroutines():
    """Deux coroutines concurrentes ont des traces isolées."""
    results = {}

    async def run_task(name: str, operation: str) -> None:
        _trace = InferenceTrace.start(operation)  # type: ignore[arg-type]
        await asyncio.sleep(0)  # yield pour laisser l'autre coroutine démarrer
        results[name] = get_active_trace()

    await asyncio.gather(
        run_task("a", "chat_turn"),
        run_task("b", "press_review"),
    )
    assert results["a"] is not results["b"]
    assert results["a"].operation == "chat_turn"
    assert results["b"].operation == "press_review"
