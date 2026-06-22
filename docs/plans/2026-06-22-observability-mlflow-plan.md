# Observabilité LLM — MLflow + Latences Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Instrumenter les latences d'inférence LLM de NewsFoundry et les persister dans MLflow (service Railway) via un `InferenceTrace` propagé par `contextvars`.

**Architecture:** Un objet `InferenceTrace` est créé au début de chaque opération métier (chat turn / press review) et propagé automatiquement via `contextvars.ContextVar`. Les fonctions `call_llm`, `call_llm_structured`, `get_top_news`, `search_news` et `compact_history_if_needed` y accumulent leurs métriques sans couplage. L'endpoint flush vers MLflow à la fin dans un `try/finally`.

**Tech Stack:** Python `contextvars`, `mlflow>=2.14`, `time.perf_counter()`, FastAPI, Railway volume (SQLite backend MLflow)

**Spec :** `docs/plans/2026-06-22-observability-mlflow-design.md`

---

## Fichiers touchés

| Fichier | Action | Rôle |
|---|---|---|
| `backend/src/core/observability.py` | Créer | `InferenceTrace`, `ContextVar`, flush MLflow + logs |
| `backend/tests/test_observability.py` | Créer | Tests unitaires et intégration MLflow |
| `backend/pyproject.toml` | Modifier | Ajouter dépendance `mlflow` |
| `backend/src/core/config.py` | Modifier | Ajouter `MLFLOW_TRACKING_URI` |
| `backend/src/core/llm_provider.py` | Modifier | `call_llm`, `call_llm_structured`, `compact_history_if_needed` |
| `backend/src/core/agent/tools.py` | Modifier | `get_top_news`, `search_news` |
| `backend/src/api/chat_endpoints.py` | Modifier | `_process_message`, `generate_chat_review` |

---

## Task 1 : Dépendance MLflow + variable de config

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/src/core/config.py`

- [ ] **Step 1 : Ajouter `mlflow` dans les dépendances**

Dans `backend/pyproject.toml`, ajouter dans la liste `dependencies` :

```toml
dependencies = [
    "fastapi>=0.136.1",
    "uvicorn[standard]>=0.46.0",
    "sqlmodel>=0.0.38",
    "psycopg2-binary>=2.9.12",
    "bcrypt>=5.0.0",
    "python-dotenv>=1.2.2",
    "python-jose[cryptography]>=3.3.0",
    "python-multipart>=0.0.28",
    "alembic>=1.18.4",
    "openai>=2.36.0",
    "sentry-sdk>=2.60.0",
    "openai-agents>=0.17.4",
    "httpx[socks]>=0.28.1",
    "worldnewsapi>=2.2.0",
    "llama-index-core>=0.12",
    "llama-index-embeddings-fastembed>=0.2",
    "fastembed>=0.4",
    "mlflow>=2.14",
]
```

- [ ] **Step 2 : Installer la dépendance**

```bash
cd backend && uv sync
```

Résultat attendu : `mlflow` et ses dépendances installés sans erreur.

- [ ] **Step 3 : Ajouter `MLFLOW_TRACKING_URI` dans config**

Dans `backend/src/core/config.py`, ajouter après le bloc `# LLM Provider` existant (après la ligne `LLM_TIMEOUT_SECONDS`) :

```python
# Observability / MLflow
# Si absent ou vide, le tracking MLflow est désactivé (mode no-op silencieux).
MLFLOW_TRACKING_URI: str | None = os.getenv("MLFLOW_TRACKING_URI") or None
```

- [ ] **Step 4 : Vérifier que les tests existants passent toujours**

```bash
cd backend && uv run pytest tests/ -x -q
```

Résultat attendu : tous les tests passent (aucune régression de l'ajout de config).

- [ ] **Step 5 : Commit**

```bash
git add backend/pyproject.toml backend/src/core/config.py
git commit -m "feat(observability): ajouter dépendance mlflow et MLFLOW_TRACKING_URI"
```

---

## Task 2 : Créer `InferenceTrace` — mode no-op (sans MLflow)

**Files:**
- Create: `backend/src/core/observability.py`
- Create: `backend/tests/test_observability.py`

- [ ] **Step 1 : Écrire les tests no-op (mode sans MLflow)**

Créer `backend/tests/test_observability.py` :

```python
"""Tests de InferenceTrace — mode no-op (MLFLOW_TRACKING_URI absent)."""
import asyncio
import os
import pytest

# Garantir que MLflow est désactivé pour ces tests
os.environ.pop("MLFLOW_TRACKING_URI", None)

from core.observability import InferenceTrace, get_active_trace


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
        trace = InferenceTrace.start(operation)  # type: ignore[arg-type]
        await asyncio.sleep(0)  # yield pour laisser l'autre coroutine démarrer
        results[name] = get_active_trace()

    await asyncio.gather(
        run_task("a", "chat_turn"),
        run_task("b", "press_review"),
    )
    assert results["a"] is not results["b"]
    assert results["a"].operation == "chat_turn"
    assert results["b"].operation == "press_review"
```

- [ ] **Step 2 : Vérifier que les tests échouent (fichier absent)**

```bash
cd backend && uv run pytest tests/test_observability.py -v
```

Résultat attendu : `ModuleNotFoundError: No module named 'core.observability'`

- [ ] **Step 3 : Implémenter `observability.py`**

Créer `backend/src/core/observability.py` :

```python
"""Instrumentation des latences d'inférence LLM.

`InferenceTrace` est propagé via `contextvars.ContextVar` — isolation automatique
entre coroutines asyncio concurrentes. Les fonctions record_* sont des no-ops si
aucune trace n'est active dans le contexte courant.
"""
from __future__ import annotations

import logging
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Literal

_logger = logging.getLogger(__name__)

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
        self._tool_records.append(_ToolRecord(tool_name=tool_name, duration_s=duration_s))
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
        model = self._llm_records[0].model if self._llm_records else "unknown"

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

        # MLflow — no-op si MLFLOW_TRACKING_URI absent
        from core.config import MLFLOW_TRACKING_URI  # import tardif pour éviter le cycle

        if not MLFLOW_TRACKING_URI:
            return

        try:
            import mlflow

            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            mlflow.set_experiment(f"newsfoundry/{self.operation}")

            with mlflow.start_run():
                mlflow.set_tags({"chat_id": str(chat_id), "model": model})

                if self.operation == "chat_turn":
                    mlflow.log_metrics(
                        {
                            "e2e_latency_s": round(e2e, 3),
                            "llm_calls_count": float(len(self._llm_records)),
                            "input_tokens_total": float(input_tokens_total),
                            "output_tokens_total": float(output_tokens_total),
                            "tok_per_sec": tok_per_sec,
                            "tool_calls_count": float(len(self._tool_records)),
                            "tool_latency_s": round(tool_latency, 3),
                            "was_compacted": float(int(self._was_compacted)),
                            "history_length": float(self._history_length),
                        }
                    )
                else:
                    mlflow.log_metrics(
                        {
                            "e2e_latency_s": round(e2e, 3),
                            "input_tokens": float(input_tokens_total),
                            "output_tokens": float(output_tokens_total),
                            "tok_per_sec": tok_per_sec,
                            "articles_count": float(articles_count),
                        }
                    )
        except Exception as exc:
            _logger.warning("[observability] MLflow flush failed: %s", exc)


def get_active_trace() -> InferenceTrace | None:
    """Retourne la trace active dans le contexte asyncio courant, ou None."""
    return _active_trace.get()
```

- [ ] **Step 4 : Lancer les tests et vérifier qu'ils passent**

```bash
cd backend && uv run pytest tests/test_observability.py -v
```

Résultat attendu : tous les tests `PASSED`.

- [ ] **Step 5 : Commit**

```bash
git add backend/src/core/observability.py backend/tests/test_observability.py
git commit -m "feat(observability): créer InferenceTrace avec propagation contextvars"
```

---

## Task 3 : Test d'intégration MLflow (flush avec tracking réel)

**Files:**
- Modify: `backend/tests/test_observability.py`

- [ ] **Step 1 : Ajouter les tests d'intégration MLflow**

Ajouter à la fin de `backend/tests/test_observability.py` :

```python
@pytest.fixture
def mlflow_file_tracking(tmp_path, monkeypatch):
    """Configure MLflow avec un tracking URI fichier temporaire."""
    tracking_uri = f"file://{tmp_path}/mlruns"
    # Patcher directement l'attribut du module config — flush() y accède via
    # `from core.config import MLFLOW_TRACKING_URI` au moment de l'appel.
    monkeypatch.setattr("core.config.MLFLOW_TRACKING_URI", tracking_uri)
    return tracking_uri


def test_flush_chat_turn_creates_mlflow_run(mlflow_file_tracking):
    import mlflow

    mlflow.set_tracking_uri(mlflow_file_tracking)
    mlflow.set_experiment("newsfoundry/chat_turn")

    trace = InferenceTrace.start("chat_turn")
    trace.record_llm(input_tokens=500, output_tokens=120, duration_s=3.0, model="qwen3-8b")
    trace.record_tool(tool_name="get_top_news", duration_s=2.5)
    trace.record_compaction(was_compacted=False, history_length=6)
    trace.flush(chat_id=99)

    runs = mlflow.search_runs(experiment_names=["newsfoundry/chat_turn"])
    assert len(runs) == 1
    assert runs.iloc[0]["metrics.e2e_latency_s"] > 0
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
    trace.record_llm(input_tokens=2000, output_tokens=800, duration_s=12.0, model="qwen3-8b")
    trace.flush(chat_id=42, articles_count=5)

    runs = mlflow.search_runs(experiment_names=["newsfoundry/press_review"])
    assert len(runs) == 1
    assert runs.iloc[0]["metrics.input_tokens"] == 2000
    assert runs.iloc[0]["metrics.output_tokens"] == 800
    assert runs.iloc[0]["metrics.articles_count"] == 5


def test_flush_swallows_mlflow_error(monkeypatch):
    """flush() ne propage pas les exceptions MLflow."""
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "http://localhost:9999")
    import importlib
    import core.config as cfg
    importlib.reload(cfg)

    trace = InferenceTrace.start("chat_turn")
    trace.record_llm(input_tokens=100, output_tokens=50, duration_s=1.0, model="qwen3")
    trace.flush(chat_id=1)  # MLflow inaccessible — ne doit pas lever

    importlib.reload(cfg)
```

- [ ] **Step 2 : Lancer les tests d'intégration**

```bash
cd backend && uv run pytest tests/test_observability.py -v
```

Résultat attendu : tous les tests `PASSED`, y compris les intégrations MLflow fichier.

- [ ] **Step 3 : Commit**

```bash
git add backend/tests/test_observability.py
git commit -m "test(observability): ajouter tests d'intégration MLflow avec tracking fichier"
```

---

## Task 4 : Injection dans `llm_provider.py`

**Files:**
- Modify: `backend/src/core/llm_provider.py`

- [ ] **Step 1 : Injecter dans `call_llm`**

Dans `backend/src/core/llm_provider.py`, importer `time` en tête de fichier (s'il n'est pas déjà importé) et ajouter l'import de `get_active_trace` :

```python
import time
from core.observability import get_active_trace
```

Modifier la fonction `call_llm` (lignes 101-138). Remplacer le bloc `async with _semaphore:` jusqu'à la fin de la fonction :

```python
    t0 = time.perf_counter()
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
    duration = time.perf_counter() - t0

    choice = completion.choices[0]
    usage = completion.usage

    trace = get_active_trace()
    if trace is not None:
        trace.record_llm(
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            duration_s=duration,
            model=completion.model,
        )

    return LLMResponse(
        content=choice.message.content or "",
        model=completion.model,
        input_tokens=usage.prompt_tokens if usage else 0,
        output_tokens=usage.completion_tokens if usage else 0,
    )
```

- [ ] **Step 2 : Injecter dans `call_llm_structured`**

Modifier `call_llm_structured` (lignes 141-175). Remplacer le bloc `async with _semaphore:` jusqu'à la fin :

```python
    t0 = time.perf_counter()
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
    duration = time.perf_counter() - t0

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("LLM returned an empty structured response")

    usage = completion.usage
    trace = get_active_trace()
    if trace is not None:
        trace.record_llm(
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            duration_s=duration,
            model=completion.model,
        )

    return parsed
```

- [ ] **Step 3 : Injecter dans `compact_history_if_needed`**

Dans `compact_history_if_needed`, après la vérification du seuil (ligne 227), appeler `record_compaction` dans les deux branches. Remplacer :

```python
    if current_tokens <= compact_threshold or len(messages) <= LLM_COMPACT_RECENT_KEEP:
        return messages, _build_context_info(messages, was_compacted=False)
```

Par :

```python
    if current_tokens <= compact_threshold or len(messages) <= LLM_COMPACT_RECENT_KEEP:
        trace = get_active_trace()
        if trace is not None:
            trace.record_compaction(was_compacted=False, history_length=len(messages))
        return messages, _build_context_info(messages, was_compacted=False)
```

Et après la construction de `compacted` (avant le `return` final), ajouter :

```python
    compacted = [summary_message, *recent]
    trace = get_active_trace()
    if trace is not None:
        trace.record_compaction(was_compacted=True, history_length=len(messages))
    return compacted, _build_context_info(compacted, was_compacted=True)
```

- [ ] **Step 4 : Lancer tous les tests pour détecter les régressions**

```bash
cd backend && uv run pytest tests/ -x -q
```

Résultat attendu : tous les tests passent.

- [ ] **Step 5 : Commit**

```bash
git add backend/src/core/llm_provider.py
git commit -m "feat(observability): injecter record_llm et record_compaction dans llm_provider"
```

---

## Task 5 : Injection dans `tools.py`

**Files:**
- Modify: `backend/src/core/agent/tools.py`

- [ ] **Step 1 : Ajouter les imports**

En tête de `backend/src/core/agent/tools.py`, ajouter :

```python
import time
from core.observability import get_active_trace
```

- [ ] **Step 2 : Injecter dans `get_top_news`**

Modifier la fonction `get_top_news`. Encadrer l'appel à `api.top_news` avec un chronomètre et appeler `record_tool` :

```python
    t0 = time.perf_counter()
    response = await asyncio.to_thread(
        api.top_news,
        source_country=source_country,
        language=language,
        var_date=effective_date,
        _request_timeout=(5, 25),
    )
    tool_duration = time.perf_counter() - t0

    trace = get_active_trace()
    if trace is not None:
        trace.record_tool(tool_name="get_top_news", duration_s=tool_duration)

    clusters = reduce_clusters(response, top_n=TOP_NEWS_CLUSTERS)
    # ... reste inchangé
```

- [ ] **Step 3 : Injecter dans `search_news`**

Même pattern dans `search_news` :

```python
    t0 = time.perf_counter()
    articles = await _search_news(
        query=query, language=language, max_results=max_results
    )
    tool_duration = time.perf_counter() - t0

    trace = get_active_trace()
    if trace is not None:
        trace.record_tool(tool_name="search_news", duration_s=tool_duration)

    if not articles:
        # ... reste inchangé
```

- [ ] **Step 4 : Lancer les tests**

```bash
cd backend && uv run pytest tests/ -x -q
```

Résultat attendu : tous les tests passent.

- [ ] **Step 5 : Commit**

```bash
git add backend/src/core/agent/tools.py
git commit -m "feat(observability): injecter record_tool dans get_top_news et search_news"
```

---

## Task 6 : Injection dans `chat_endpoints.py`

**Files:**
- Modify: `backend/src/api/chat_endpoints.py`

- [ ] **Step 1 : Ajouter l'import**

En tête de `backend/src/api/chat_endpoints.py`, ajouter dans les imports :

```python
from core.observability import InferenceTrace
```

- [ ] **Step 2 : Instrumenter `_process_message` (chat turn)**

Dans la fonction `_process_message`, envelopper le corps de la fonction avec `InferenceTrace`. Ajouter après `now = datetime.now(timezone.utc).isoformat()` :

```python
    trace = InferenceTrace.start("chat_turn")
```

Et remplacer le bloc `try: result = await asyncio.wait_for(...)` jusqu'à la fin de la fonction par :

```python
    try:
        result = await asyncio.wait_for(
            Runner.run(active_agent, input=openai_messages, context=run_context),
            timeout=LLM_TIMEOUT_SECONDS,
        )
        response_content = result.final_output
    except asyncio.TimeoutError:
        logger.error(
            "[chat] LLM timeout after %.1fs — chat_id=%s base_url=%s model=%s",
            LLM_TIMEOUT_SECONDS,
            chat_id,
            LLM_BASE_URL,
            LLM_MODEL,
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="LLM request timed out"
        )
    except Exception as exc:
        logger.error(
            "[chat] LLM provider error — chat_id=%s exc=%r base_url=%s model=%s",
            chat_id,
            exc,
            LLM_BASE_URL,
            LLM_MODEL,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="LLM provider error"
        )
    finally:
        trace.flush(chat_id=chat_id)

    # Fusionner les articles collectés avec les existants (dédupliqués par URL)
    if run_context.loaded_articles:
        existing: list[dict] = chat.loaded_articles or []
        existing_urls = {a.get("url") for a in existing if a.get("url")}
        merged = existing + [
            a for a in run_context.loaded_articles if a["url"] not in existing_urls
        ]
        await asyncio.to_thread(update_chat_loaded_articles_sync, chat_id, merged)

    # Persist AI response
    ai_timestamp = datetime.now(timezone.utc).isoformat()
    ai_msg = await asyncio.to_thread(
        create_message_sync,
        chat_id,
        response_content,
        ai_timestamp,
        MessageType.AI,
    )

    return SendMessageResponse(
        chat_id=chat_id,
        message=MessagePublic(
            id=ai_msg.id,  # type: ignore[arg-type]
            chat_id=ai_msg.chat_id,
            type=ai_msg.type.value,
            content=ai_msg.content,
            timestamp=ai_msg.timestamp,
        ),
        context=ctx_info,
    )
```

> Note : `trace.flush()` est dans le `finally` — il s'exécute même en cas de timeout ou d'erreur, ce qui permet de mesurer les latences des cas d'échec aussi.

- [ ] **Step 3 : Instrumenter `generate_chat_review`**

Dans `generate_chat_review`, ajouter juste après la récupération de `messages` (après le check `if not messages`) :

```python
        trace = InferenceTrace.start("press_review")
```

Et remplacer le bloc `try: result = await asyncio.wait_for(Runner.run(active_review_agent...))` par :

```python
        try:
            result = await asyncio.wait_for(
                Runner.run(active_review_agent, input=llm_messages),
                timeout=LLM_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.error("[review] LLM timeout — chat_id=%s", chat_id)
            raise HTTPException(status_code=504, detail="LLM request timed out")
        except Exception as exc:
            logger.error(
                "[review] LLM provider error — chat_id=%s exc=%r", chat_id, exc
            )
            raise HTTPException(status_code=502, detail="LLM provider error")
        finally:
            trace.flush(chat_id=chat_id, articles_count=len(all_articles))
```

- [ ] **Step 4 : Lancer tous les tests**

```bash
cd backend && uv run pytest tests/ -x -q
```

Résultat attendu : tous les tests passent.

- [ ] **Step 5 : Commit**

```bash
git add backend/src/api/chat_endpoints.py
git commit -m "feat(observability): démarrer et flusher InferenceTrace dans les endpoints"
```

---

## Task 7 : Déploiement du service MLflow sur Railway

**Files:**
- Aucun fichier code — configuration Railway via UI ou CLI

- [ ] **Step 1 : Créer le service MLflow sur Railway**

Dans le dashboard Railway du projet NewsFoundry :
1. Cliquer **New Service → Empty Service**
2. Nommer le service `mlflow`
3. Dans **Settings → Source**, choisir **Docker Image**
4. Image : `ghcr.io/mlflow/mlflow:latest`
5. Start command :
   ```
   mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:////mlflow/mlruns.db --default-artifact-root /mlflow/artifacts
   ```

- [ ] **Step 2 : Attacher un volume persistant**

Dans le service `mlflow` sur Railway :
1. Aller dans **Volumes**
2. Cliquer **Add Volume**
3. Mount path : `/mlflow`
4. Déployer le service

- [ ] **Step 3 : Vérifier que MLflow démarre**

Dans les logs Railway du service `mlflow`, vérifier la présence de :
```
[INFO] Listening at: http://0.0.0.0:5000
```

- [ ] **Step 4 : Configurer la variable d'env dans le backend Railway**

Dans le service `backend` Railway, ajouter la variable d'environnement :
```
MLFLOW_TRACKING_URI=http://mlflow.railway.internal:5000
```

> Note : Railway résout automatiquement `mlflow.railway.internal` vers l'IP interne du service `mlflow` dans le même projet. Adapter le nom si le service Railway s'appelle autrement.

- [ ] **Step 5 : Redéployer le backend et vérifier les logs**

Après redéploiement, envoyer un message de chat via l'application. Dans les logs Railway du backend, vérifier la présence de lignes :
```
[observability] llm_call duration_s=... input=... output=... tok/s=... model=...
[observability] chat_turn_complete chat_id=... e2e=...s ...
```

- [ ] **Step 6 : Vérifier dans l'UI MLflow**

Générer un domaine public pour le service `mlflow` Railway (Settings → Networking → Generate Domain), puis ouvrir l'URL. Vérifier la présence de l'expérience `newsfoundry/chat_turn` avec des runs.

- [ ] **Step 7 : Commit de documentation**

```bash
git add docs/plans/2026-06-22-observability-mlflow-plan.md
git commit -m "docs: finaliser plan observabilité avec étapes déploiement Railway MLflow"
```

---

## Récapitulatif des métriques disponibles après implémentation

| Métrique | Disponible dans | Visible dans |
|---|---|---|
| `e2e_latency_s` | MLflow + logs Railway | MLflow UI + Railway Logs |
| `llm_calls_count` | MLflow + logs Railway | MLflow UI |
| `input_tokens_total` | MLflow + logs Railway | MLflow UI |
| `output_tokens_total` | MLflow + logs Railway | MLflow UI |
| `tok_per_sec` | MLflow + logs Railway | MLflow UI + Railway Logs |
| `tool_calls_count` | MLflow | MLflow UI |
| `tool_latency_s` | MLflow + logs Railway | MLflow UI + Railway Logs |
| `was_compacted` | MLflow + logs Railway | MLflow UI |
| `history_length` | MLflow | MLflow UI |
| `articles_count` | MLflow | MLflow UI |
