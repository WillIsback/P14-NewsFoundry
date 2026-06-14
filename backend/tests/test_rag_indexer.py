"""Tests unitaires pour core.rag.indexer.

Utilise MockEmbedding de LlamaIndex pour éviter de charger le modèle HuggingFace.
"""

import sys
from pathlib import Path

import pytest

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))


@pytest.fixture(autouse=True)
def patch_embed(monkeypatch):
    """Remplace le singleton HuggingFace par MockEmbedding (384 dims)."""
    from llama_index.core.embeddings import MockEmbedding

    mock = MockEmbedding(embed_dim=384)
    monkeypatch.setattr("core.rag.indexer._embed", mock)


_ARTICLES = [
    {
        "title": "Conflit en Iran",
        "summary": "Les tensions s'intensifient au Moyen-Orient entre l'Iran et Israël.",
        "url": "https://example.com/iran",
    },
    {
        "title": "Élection présidentielle en France",
        "summary": "Les sondages donnent la gauche en tête à deux semaines du scrutin.",
        "url": "https://example.com/france",
    },
    {
        "title": "Intelligence artificielle : OpenAI sort GPT-5",
        "summary": "OpenAI a présenté son dernier modèle lors d'une conférence à San Francisco.",
        "url": "https://example.com/ia",
    },
]


def test_returns_list_of_dicts():
    from core.rag.indexer import build_index_and_retrieve

    results = build_index_and_retrieve(_ARTICLES, "Iran Moyen-Orient", top_k=2)
    assert isinstance(results, list)
    for item in results:
        assert "title" in item
        assert "summary" in item
        assert "url" in item


def test_returns_at_most_top_k_items():
    from core.rag.indexer import build_index_and_retrieve

    results = build_index_and_retrieve(_ARTICLES, "actualités", top_k=2)
    assert len(results) <= 2


def test_top_k_greater_than_articles_does_not_crash():
    from core.rag.indexer import build_index_and_retrieve

    results = build_index_and_retrieve(_ARTICLES, "actualités", top_k=100)
    assert len(results) <= len(_ARTICLES)


def test_empty_articles_returns_empty_list():
    from core.rag.indexer import build_index_and_retrieve

    results = build_index_and_retrieve([], "Iran", top_k=5)
    assert results == []


def test_caps_at_max_articles(monkeypatch):
    from core.rag import indexer

    monkeypatch.setattr(indexer, "_MAX_ARTICLES", 2)
    many = _ARTICLES * 5  # 15 articles
    from core.rag.indexer import build_index_and_retrieve

    results = build_index_and_retrieve(many, "actualités", top_k=10)
    assert len(results) <= 2


def test_all_returned_urls_come_from_input():
    from core.rag.indexer import build_index_and_retrieve

    input_urls = {a["url"] for a in _ARTICLES}
    results = build_index_and_retrieve(_ARTICLES, "France politique", top_k=3)
    for item in results:
        assert item["url"] in input_urls
