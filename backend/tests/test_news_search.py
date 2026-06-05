"""
Tests for core.news.search — search_news service layer.
---------------------------------------------------------
Unit tests: mock worldnewsapi, aucun appel réseau ni LLM.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from worldnewsapi.models.search_news200_response import SearchNews200Response
from worldnewsapi.models.search_news200_response_news_inner import (
    SearchNews200ResponseNewsInner,
)

from core.news.search import SearchArticle, search_news


# ── helpers ───────────────────────────────────────────────────────────────────


def _make_news_inner(
    id_: int = 1,
    title: str = "Article test",
    url: str = "https://example.com/1",
    summary: str = "Résumé test.",
    publish_date: str = "2026-06-05 08:00:00",
    source_country: str = "fr",
) -> SearchNews200ResponseNewsInner:
    return SearchNews200ResponseNewsInner(
        id=id_,
        title=title,
        url=url,
        summary=summary,
        text="Texte complet.",
        publish_date=publish_date,
        authors=["Auteur Test"],
        language="fr",
        source_country=source_country,
        category="technology",
        sentiment=0.1,
    )


def _fake_api_response(articles: list[SearchNews200ResponseNewsInner]) -> SearchNews200Response:
    return SearchNews200Response(
        offset=0,
        number=len(articles),
        available=len(articles),
        news=articles,
    )


# ── Unit tests ────────────────────────────────────────────────────────────────


class TestSearchNews:
    """Teste la fonction search_news du service."""

    @pytest.fixture
    def mock_api(self):
        api = MagicMock()
        api.search_news.return_value = _fake_api_response(
            [
                _make_news_inner(id_=1, title="Article IA", url="https://ex.com/1"),
                _make_news_inner(id_=2, title="Article Éco", url="https://ex.com/2"),
            ]
        )
        return api

    @pytest.mark.asyncio
    async def test_returns_list_of_search_articles(self, mock_api):
        with patch("core.news.search.get_news_api", return_value=mock_api):
            results = await search_news(query="intelligence artificielle")
        assert isinstance(results, list)
        assert len(results) == 2
        assert all(isinstance(a, SearchArticle) for a in results)

    @pytest.mark.asyncio
    async def test_articles_have_title_url_summary(self, mock_api):
        with patch("core.news.search.get_news_api", return_value=mock_api):
            results = await search_news(query="IA")
        assert results[0].title == "Article IA"
        assert results[0].url == "https://ex.com/1"
        assert results[1].title == "Article Éco"

    @pytest.mark.asyncio
    async def test_empty_result_returns_empty_list(self):
        empty_api = MagicMock()
        empty_api.search_news.return_value = _fake_api_response([])
        with patch("core.news.search.get_news_api", return_value=empty_api):
            results = await search_news(query="sujetinexistant")
        assert results == []

    @pytest.mark.asyncio
    async def test_forwards_language_param(self, mock_api):
        with patch("core.news.search.get_news_api", return_value=mock_api):
            await search_news(query="énergie", language="fr")
        call_kwargs = mock_api.search_news.call_args.kwargs
        assert call_kwargs.get("language") == "fr"

    @pytest.mark.asyncio
    async def test_forwards_max_results_as_number(self, mock_api):
        with patch("core.news.search.get_news_api", return_value=mock_api):
            await search_news(query="sport", max_results=7)
        call_kwargs = mock_api.search_news.call_args.kwargs
        assert call_kwargs.get("number") == 7

    @pytest.mark.asyncio
    async def test_max_results_capped_at_20(self, mock_api):
        with patch("core.news.search.get_news_api", return_value=mock_api):
            await search_news(query="sport", max_results=99)
        call_kwargs = mock_api.search_news.call_args.kwargs
        assert call_kwargs.get("number") <= 20

    @pytest.mark.asyncio
    async def test_sorts_by_publish_time_descending(self, mock_api):
        with patch("core.news.search.get_news_api", return_value=mock_api):
            await search_news(query="actualité")
        call_kwargs = mock_api.search_news.call_args.kwargs
        assert call_kwargs.get("sort") == "publish-time"
        assert call_kwargs.get("sort_direction") == "DESC"

    @pytest.mark.asyncio
    async def test_article_summary_is_empty_string_when_none(self):
        api = MagicMock()
        article = _make_news_inner(id_=1, title="T", url="http://x.com", summary=None)
        api.search_news.return_value = _fake_api_response([article])
        with patch("core.news.search.get_news_api", return_value=api):
            results = await search_news(query="test")
        assert results[0].summary == ""

    @pytest.mark.asyncio
    async def test_article_publish_date_is_empty_string_when_none(self):
        api = MagicMock()
        article = _make_news_inner(id_=1, publish_date=None)
        api.search_news.return_value = _fake_api_response([article])
        with patch("core.news.search.get_news_api", return_value=api):
            results = await search_news(query="test")
        assert results[0].publish_date == ""


class TestSearchArticleModel:
    """Teste le modèle SearchArticle."""

    def test_all_fields_present(self):
        a = SearchArticle(
            title="Titre",
            url="https://example.com",
            summary="Résumé",
            publish_date="2026-06-05 08:00:00",
            source_country="fr",
        )
        assert a.title == "Titre"
        assert a.url == "https://example.com"
        assert a.summary == "Résumé"
        assert a.publish_date == "2026-06-05 08:00:00"
        assert a.source_country == "fr"

    def test_optional_fields_default_to_empty_string(self):
        a = SearchArticle(title="T", url="http://x.com")
        assert a.summary == ""
        assert a.publish_date == ""
        assert a.source_country == ""
