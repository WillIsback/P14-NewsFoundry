"""Tests de InferenceTrace — mode no-op (MLFLOW_TRACKING_URI absent)."""

import asyncio
import os
import pytest

# Garantir que MLflow est désactivé pour ces tests
os.environ.pop("MLFLOW_TRACKING_URI", None)

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


def test_flush_no_op_without_mlflow_uri(caplog):
    """flush() ne lève pas d'exception quand MLFLOW_TRACKING_URI est absent."""
    trace = InferenceTrace.start("chat_turn")
    trace.record_llm(input_tokens=100, output_tokens=50, duration_s=1.0, model="qwen3")
    trace.flush(chat_id=1)  # ne doit pas lever


def test_flush_press_review_no_op(caplog):
    """flush() pour press_review ne lève pas d'exception sans MLflow."""
    trace = InferenceTrace.start("press_review")
    trace.record_llm(input_tokens=800, output_tokens=400, duration_s=5.0, model="qwen3")
    trace.flush(chat_id=2, articles_count=3)


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


# ---------------------------------------------------------------------------
# Tests d'intégration MLflow (tracking URI fichier — pas de serveur requis)
# ---------------------------------------------------------------------------


@pytest.fixture
def mlflow_file_tracking(tmp_path, monkeypatch):
    """Configure MLflow avec un tracking URI SQLite temporaire.

    mlflow>=3.0 a déprécié le backend file:// — on utilise sqlite:// à la place
    (toujours local, pas de serveur requis).
    """
    tracking_uri = f"sqlite:///{tmp_path}/mlruns.db"
    # Patcher directement l'attribut du module config — flush() y accède via
    # `from core.config import MLFLOW_TRACKING_URI` au moment de l'appel.
    monkeypatch.setattr("core.config.MLFLOW_TRACKING_URI", tracking_uri)
    return tracking_uri


def test_flush_chat_turn_creates_mlflow_run(mlflow_file_tracking):
    import mlflow

    mlflow.set_tracking_uri(mlflow_file_tracking)
    mlflow.set_experiment("newsfoundry/chat_turn")

    trace = InferenceTrace.start("chat_turn")
    trace.record_llm(
        input_tokens=500, output_tokens=120, duration_s=3.0, model="qwen3-8b"
    )
    trace.record_tool(tool_name="get_top_news", duration_s=2.5)
    trace.record_compaction(was_compacted=False, history_length=6)
    trace.flush(chat_id=99)

    runs = mlflow.search_runs(experiment_names=["newsfoundry/chat_turn"])
    assert len(runs) == 1
    assert runs.iloc[0]["metrics.e2e_latency_s"] >= 0
    assert runs.iloc[0]["metrics.input_tokens_total"] == 500
    assert runs.iloc[0]["metrics.output_tokens_total"] == 120
    assert runs.iloc[0]["metrics.tool_calls_count"] == 1
    assert runs.iloc[0]["metrics.was_compacted"] == 0
    assert runs.iloc[0]["metrics.history_length"] == 6
    assert runs.iloc[0]["tags.chat_id"] == "99"


def test_flush_press_review_creates_mlflow_run(mlflow_file_tracking):
    import mlflow

    mlflow.set_tracking_uri(mlflow_file_tracking)
    mlflow.set_experiment("newsfoundry/press_review")

    trace = InferenceTrace.start("press_review")
    trace.record_llm(
        input_tokens=2000, output_tokens=800, duration_s=12.0, model="qwen3-8b"
    )
    trace.flush(chat_id=42, articles_count=5)

    runs = mlflow.search_runs(experiment_names=["newsfoundry/press_review"])
    assert len(runs) == 1
    assert runs.iloc[0]["metrics.input_tokens"] == 2000
    assert runs.iloc[0]["metrics.output_tokens"] == 800
    assert runs.iloc[0]["metrics.articles_count"] == 5


def test_flush_swallows_mlflow_error(monkeypatch):
    """flush() ne propage pas les exceptions MLflow (serveur inaccessible)."""
    monkeypatch.setattr("core.config.MLFLOW_TRACKING_URI", "http://localhost:9999")

    trace = InferenceTrace.start("chat_turn")
    trace.record_llm(input_tokens=100, output_tokens=50, duration_s=1.0, model="qwen3")
    trace.flush(chat_id=1)  # MLflow inaccessible — ne doit pas lever
