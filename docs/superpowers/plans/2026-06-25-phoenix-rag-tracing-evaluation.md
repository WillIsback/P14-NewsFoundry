# Phoenix RAG Tracing & Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter des spans OpenInference RETRIEVER et CHAIN dans le pipeline RAG et revue de presse pour permettre l'évaluation via Phoenix Experiments.

**Architecture:** Deux context managers (`rag_span`, `press_review_span`) sont ajoutés dans `observability.py` et utilisés dans `chat_endpoints.py`. Aucune nouvelle dépendance — le tracer OTel est déjà initialisé dans `telemetry.py`. L'évaluation se fait entièrement dans l'UI Phoenix via Datasets + Experiments.

**Tech Stack:** OpenTelemetry SDK (déjà présent), OpenInference conventions pour les attributs de span, pytest + `InMemorySpanExporter` pour les tests.

---

## File Map

| Fichier | Action | Responsabilité |
|---------|--------|----------------|
| `backend/src/core/observability.py` | Modifier | Ajouter `rag_span()` et `press_review_span()` |
| `backend/src/api/chat_endpoints.py` | Modifier | Utiliser les deux context managers dans `generate_chat_review()` |
| `backend/tests/test_observability_spans.py` | Créer | Tests TDD des deux nouveaux context managers |

---

## Task 1 : Span RETRIEVER pour le RAG

**Files:**
- Modify: `backend/src/core/observability.py`
- Create: `backend/tests/test_observability_spans.py`

- [ ] **Step 1 : Écrire le test RED**

Créer `backend/tests/test_observability_spans.py` :

```python
"""Tests TDD pour les context managers de spans OTel — rag_span et press_review_span."""

import json
from pathlib import Path
import sys

import pytest
from opentelemetry import trace as otel_trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))


@pytest.fixture()
def span_exporter(monkeypatch):
    """Injecte un TracerProvider in-memory et retourne l'exporter pour assertion."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    import core.observability as obs
    monkeypatch.setattr(obs, "_tracer", provider.get_tracer("newsfoundry-test"))
    yield exporter
    exporter.clear()


# ---------------------------------------------------------------------------
# rag_span
# ---------------------------------------------------------------------------

def test_rag_span_name(span_exporter):
    from core.observability import rag_span

    with rag_span(query="actualités France", top_k=5):
        pass

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "rag_retrieve"


def test_rag_span_openinference_kind(span_exporter):
    from core.observability import rag_span

    with rag_span(query="actualités France", top_k=5):
        pass

    span = span_exporter.get_finished_spans()[0]
    attrs = dict(span.attributes)
    assert attrs["openinference.span.kind"] == "RETRIEVER"


def test_rag_span_input_and_top_k(span_exporter):
    from core.observability import rag_span

    with rag_span(query="conflit au Moyen-Orient", top_k=3):
        pass

    attrs = dict(span_exporter.get_finished_spans()[0].attributes)
    assert attrs["input.value"] == "conflit au Moyen-Orient"
    assert attrs["rag.top_k"] == 3


def test_rag_span_set_retrieved_documents(span_exporter):
    from core.observability import rag_span

    articles = [
        {"title": "Article A", "url": "https://ex.com/a", "summary": "Résumé A"},
        {"title": "Article B", "url": "https://ex.com/b", "summary": "Résumé B"},
    ]

    with rag_span(query="test", top_k=5) as span:
        for i, a in enumerate(articles):
            span.set_attribute(f"retrieval.documents.{i}.document.content", a["summary"])
            span.set_attribute(f"retrieval.documents.{i}.document.metadata.url", a["url"])
            span.set_attribute(f"retrieval.documents.{i}.document.metadata.title", a["title"])
        span.set_attribute("rag.retrieved_count", len(articles))

    attrs = dict(span_exporter.get_finished_spans()[0].attributes)
    assert attrs["retrieval.documents.0.document.metadata.title"] == "Article A"
    assert attrs["retrieval.documents.1.document.metadata.url"] == "https://ex.com/b"
    assert attrs["rag.retrieved_count"] == 2
```

- [ ] **Step 2 : Vérifier que le test échoue (RED)**

```bash
cd /home/will/formation_OC/P14/NewsFoundry/backend
uv run pytest tests/test_observability_spans.py -v 2>&1 | head -30
```

Attendu : `ImportError` ou `AttributeError` — `rag_span` n'existe pas encore.

- [ ] **Step 3 : Implémenter `rag_span()` dans `observability.py`**

Ajouter en haut du fichier `backend/src/core/observability.py` (après les imports existants) :

```python
import json
from contextlib import contextmanager
from opentelemetry import trace as otel_trace

_tracer = otel_trace.get_tracer("newsfoundry")
```

> **Note :** `contextmanager` est déjà importé dans ce fichier — ne pas le dupliquer. Vérifier la ligne 14 : `from contextlib import contextmanager`. Ajouter uniquement `json` et `otel_trace` s'ils ne sont pas déjà présents.

Ajouter la fonction à la fin du fichier (avant `get_active_trace`) :

```python
@contextmanager
def rag_span(query: str, top_k: int):
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
```

- [ ] **Step 4 : Vérifier que les tests RAG passent (GREEN)**

```bash
cd /home/will/formation_OC/P14/NewsFoundry/backend
uv run pytest tests/test_observability_spans.py::test_rag_span_name \
              tests/test_observability_spans.py::test_rag_span_openinference_kind \
              tests/test_observability_spans.py::test_rag_span_input_and_top_k \
              tests/test_observability_spans.py::test_rag_span_set_retrieved_documents \
              -v
```

Attendu : 4 tests PASS.

- [ ] **Step 5 : Commit**

```bash
cd /home/will/formation_OC/P14/NewsFoundry
git add backend/src/core/observability.py backend/tests/test_observability_spans.py
git commit -m "feat(otel): ajouter rag_span() context manager — span RETRIEVER Phoenix

Refs #228"
```

---

## Task 2 : Span CHAIN pour la revue de presse

**Files:**
- Modify: `backend/src/core/observability.py`
- Modify: `backend/tests/test_observability_spans.py`

- [ ] **Step 1 : Écrire les tests RED pour `press_review_span`**

Ajouter à la fin de `backend/tests/test_observability_spans.py` :

```python
# ---------------------------------------------------------------------------
# press_review_span
# ---------------------------------------------------------------------------

def test_press_review_span_name(span_exporter):
    from core.observability import press_review_span

    articles = [{"title": "T1", "url": "https://ex.com/1"}]
    with press_review_span(articles=articles):
        pass

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "press_review_generation"


def test_press_review_span_openinference_kind(span_exporter):
    from core.observability import press_review_span

    with press_review_span(articles=[{"title": "T", "url": "https://ex.com"}]):
        pass

    attrs = dict(span_exporter.get_finished_spans()[0].attributes)
    assert attrs["openinference.span.kind"] == "CHAIN"


def test_press_review_span_input_contains_articles(span_exporter):
    from core.observability import press_review_span

    articles = [
        {"title": "Article France", "url": "https://lemonde.fr/1"},
        {"title": "Article Tech", "url": "https://techcrunch.com/2"},
    ]
    with press_review_span(articles=articles):
        pass

    attrs = dict(span_exporter.get_finished_spans()[0].attributes)
    input_val = json.loads(attrs["input.value"])
    assert len(input_val) == 2
    assert input_val[0]["title"] == "Article France"
    assert input_val[1]["url"] == "https://techcrunch.com/2"


def test_press_review_span_set_output(span_exporter):
    from core.observability import press_review_span

    with press_review_span(articles=[{"title": "T", "url": "https://ex.com"}]) as span:
        span.set_attribute("output.value", "Titre éditorial — Introduction de la revue...")
        span.set_attribute("chat.articles_count", 5)

    attrs = dict(span_exporter.get_finished_spans()[0].attributes)
    assert "Titre éditorial" in attrs["output.value"]
    assert attrs["chat.articles_count"] == 5


def test_press_review_span_handles_missing_keys(span_exporter):
    """Les articles sans 'title' ou 'url' ne font pas crasher le context manager."""
    from core.observability import press_review_span

    articles = [{"title": "Seulement un titre"}, {"url": "https://ex.com/only-url"}]
    with press_review_span(articles=articles):
        pass

    attrs = dict(span_exporter.get_finished_spans()[0].attributes)
    sources = json.loads(attrs["input.value"])
    assert sources[0]["url"] == ""
    assert sources[1]["title"] == ""
```

- [ ] **Step 2 : Vérifier que les tests échouent (RED)**

```bash
cd /home/will/formation_OC/P14/NewsFoundry/backend
uv run pytest tests/test_observability_spans.py -k "press_review" -v 2>&1 | head -20
```

Attendu : `ImportError` — `press_review_span` n'existe pas.

- [ ] **Step 3 : Implémenter `press_review_span()` dans `observability.py`**

Ajouter après `rag_span` dans `backend/src/core/observability.py` :

```python
@contextmanager
def press_review_span(articles: list[dict]):
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
            {"title": a.get("title", ""), "url": a.get("url", "")}
            for a in articles
        ]
        span.set_attribute("input.value", json.dumps(sources, ensure_ascii=False))
        yield span
```

- [ ] **Step 4 : Vérifier que tous les tests passent (GREEN)**

```bash
cd /home/will/formation_OC/P14/NewsFoundry/backend
uv run pytest tests/test_observability_spans.py -v
```

Attendu : tous les tests PASS (rag + press_review).

- [ ] **Step 5 : Vérifier que les tests existants ne régressent pas**

```bash
cd /home/will/formation_OC/P14/NewsFoundry/backend
uv run pytest tests/test_observability.py -v
```

Attendu : tous les tests existants PASS.

- [ ] **Step 6 : Commit**

```bash
cd /home/will/formation_OC/P14/NewsFoundry
git add backend/src/core/observability.py backend/tests/test_observability_spans.py
git commit -m "feat(otel): ajouter press_review_span() context manager — span CHAIN Phoenix

Refs #228"
```

---

## Task 3 : Intégration dans `chat_endpoints.py`

**Files:**
- Modify: `backend/src/api/chat_endpoints.py`

> Pas de nouveau fichier de test — `generate_chat_review` est couvert par `tests/test_press_review_endpoints.py` qui mocke le Runner. On vérifie manuellement que les imports compilent et que les tests existants passent.

- [ ] **Step 1 : Vérifier l'état actuel des tests endpoints**

```bash
cd /home/will/formation_OC/P14/NewsFoundry/backend
uv run pytest tests/test_press_review_endpoints.py -v 2>&1 | tail -15
```

Attendu : tous les tests passent (baseline avant modification).

- [ ] **Step 2 : Modifier `generate_chat_review` dans `chat_endpoints.py`**

Dans `backend/src/api/chat_endpoints.py`, ligne 28, ajouter `rag_span` et `press_review_span` à l'import depuis `core.observability` :

```python
from core.observability import InferenceTrace, tracing_context, rag_span, press_review_span
```

Localiser le bloc RAG dans `generate_chat_review` (autour de la ligne 357) — actuellement :

```python
                relevant = await asyncio.to_thread(
                    build_index_and_retrieve, articles, query, top_k=5
                )
```

Remplacer ce bloc par :

```python
                with rag_span(query=query, top_k=5) as rspan:
                    relevant = await asyncio.to_thread(
                        build_index_and_retrieve, articles, query, top_k=5
                    )
                    for i, a in enumerate(relevant):
                        rspan.set_attribute(
                            f"retrieval.documents.{i}.document.content",
                            a.get("summary", ""),
                        )
                        rspan.set_attribute(
                            f"retrieval.documents.{i}.document.metadata.url",
                            a.get("url", ""),
                        )
                        rspan.set_attribute(
                            f"retrieval.documents.{i}.document.metadata.title",
                            a.get("title", ""),
                        )
                    rspan.set_attribute("rag.retrieved_count", len(relevant))
```

Localiser le bloc `Runner.run(press_review_agent)` (autour de la ligne 377) — actuellement :

```python
        with tracing_context(session_id=str(chat_id)):
            try:
                result = await asyncio.wait_for(
                    Runner.run(active_review_agent, input=llm_messages),
                    timeout=LLM_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                ...
            except Exception as exc:
                ...
            finally:
                trace.flush(chat_id=chat_id, articles_count=len(all_articles))
```

Remplacer par :

```python
        with tracing_context(session_id=str(chat_id)):
            with press_review_span(articles=all_articles) as prspan:
                try:
                    result = await asyncio.wait_for(
                        Runner.run(active_review_agent, input=llm_messages),
                        timeout=LLM_TIMEOUT_SECONDS,
                    )
                    if result.final_output:
                        prspan.set_attribute(
                            "output.value",
                            result.final_output.title
                            + " — "
                            + result.final_output.editorial[:200],
                        )
                        prspan.set_attribute("chat.articles_count", len(all_articles))
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

- [ ] **Step 3 : Vérifier que les tests endpoints passent toujours**

```bash
cd /home/will/formation_OC/P14/NewsFoundry/backend
uv run pytest tests/test_press_review_endpoints.py tests/test_observability_spans.py tests/test_observability.py -v
```

Attendu : tous les tests PASS.

- [ ] **Step 4 : Lancer la suite complète**

```bash
cd /home/will/formation_OC/P14/NewsFoundry/backend
uv run pytest tests/ -v --ignore=tests/wet_test_endpoints.py 2>&1 | tail -20
```

Attendu : aucune régression.

- [ ] **Step 5 : Commit**

```bash
cd /home/will/formation_OC/P14/NewsFoundry
git add backend/src/api/chat_endpoints.py
git commit -m "feat(otel): intégrer rag_span et press_review_span dans generate_chat_review

Spans RETRIEVER et CHAIN visibles dans Phoenix pour les Experiments d'évaluation.

Refs #228"
```

---

## Task 4 : Pull Request

- [ ] **Step 1 : Pousser la branche**

```bash
cd /home/will/formation_OC/P14/NewsFoundry
git push -u origin feat/228-phoenix-rag-tracing-evaluation
```

- [ ] **Step 2 : Créer la PR**

```bash
gh pr create \
  --title "feat(otel): spans RETRIEVER et CHAIN pour Phoenix Experiments (RAG + revue de presse)" \
  --body "$(cat <<'EOF'
## Résumé

- Ajoute `rag_span()` — span OpenInference **RETRIEVER** autour de `build_index_and_retrieve()` avec attributs `input.value`, `retrieval.documents.*`, `rag.top_k`, `rag.retrieved_count`
- Ajoute `press_review_span()` — span OpenInference **CHAIN** autour de `Runner.run(press_review_agent)` avec les articles sources et la review générée
- Intègre les deux spans dans `generate_chat_review()`
- Zéro nouvelle dépendance, zéro impact latence

## Motivation

Permet la mise en place des **Phoenix Experiments** (LLM-as-judge via vLLM local) pour évaluer la pertinence RAG et la fidélité/qualité des revues de presse, sans modifier le pipeline de prod.

## Test plan

- [ ] `pytest tests/test_observability_spans.py` — tests TDD des nouveaux context managers
- [ ] `pytest tests/test_press_review_endpoints.py` — non-régression endpoints
- [ ] `pytest tests/test_observability.py` — non-régression InferenceTrace
- [ ] Vérifier dans Phoenix UI que les spans `rag_retrieve` et `press_review_generation` apparaissent avec les bons attributs après un appel à `/chats/{id}/review`

Closes #228

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Self-Review

**Couverture spec :**
- ✅ Span RETRIEVER avec `input.value`, `retrieval.documents.*`, `rag.top_k`, `rag.retrieved_count`
- ✅ Span CHAIN avec articles sources, output, `chat.articles_count`
- ✅ `openinference.span.kind` sur les deux spans
- ✅ Zéro nouvelle dépendance Python
- ✅ Tests TDD complets pour les deux context managers
- ✅ PR mentionnant l'issue #228

**Placeholders :** aucun.

**Cohérence des types :**
- `rag_span` yielde le span → `rspan.set_attribute(...)` ✅
- `press_review_span` yielde le span → `prspan.set_attribute(...)` ✅
- `_tracer` défini dans `observability.py` et patché dans le fixture de test ✅
