"""Tests TDD pour les context managers de spans OTel — rag_span et press_review_span."""

from pathlib import Path
import sys

import pytest
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
            span.set_attribute(
                f"retrieval.documents.{i}.document.content", a["summary"]
            )
            span.set_attribute(
                f"retrieval.documents.{i}.document.metadata.url", a["url"]
            )
            span.set_attribute(
                f"retrieval.documents.{i}.document.metadata.title", a["title"]
            )
        span.set_attribute("rag.retrieved_count", len(articles))

    attrs = dict(span_exporter.get_finished_spans()[0].attributes)
    assert attrs["retrieval.documents.0.document.metadata.title"] == "Article A"
    assert attrs["retrieval.documents.1.document.metadata.url"] == "https://ex.com/b"
    assert attrs["rag.retrieved_count"] == 2
