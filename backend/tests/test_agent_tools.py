"""Tests for core.agent.tools — get_top_news and search_news function tools.

Unit tests: mock worldnewsapi, aucun appel réseau.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch


def _make_run_ctx() -> MagicMock:
    """Construit un RunContextWrapper factice suffisant pour on_invoke_tool."""
    ctx = MagicMock()
    ctx.run_config = MagicMock()
    ctx.run_config.model_settings = None
    return ctx

import pytest

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from worldnewsapi.models.top_news200_response import TopNews200Response
from worldnewsapi.models.top_news200_response_top_news_inner import (
    TopNews200ResponseTopNewsInner,
)
from worldnewsapi.models.top_news200_response_top_news_inner_news_inner import (
    TopNews200ResponseTopNewsInnerNewsInner,
)


# ── helpers ───────────────────────────────────────────────────────────────────


def _make_top_news_response(n_clusters: int = 3) -> TopNews200Response:
    clusters = []
    for i in range(n_clusters):
        articles = [
            TopNews200ResponseTopNewsInnerNewsInner(
                id=i * 10 + j,
                title=f"Titre cluster {i + 1} article {j + 1}",
                url=f"https://example.com/cluster{i + 1}/article{j + 1}",
                publish_date="2026-06-05 08:00:00",
                summary=f"Résumé cluster {i + 1}.",
                text="Texte.",
                author="Auteur Test",
            )
            for j in range(2)
        ]
        clusters.append(TopNews200ResponseTopNewsInner(news=articles))
    return TopNews200Response(top_news=clusters, language="fr", country="fr")


# ── Tests get_top_news ────────────────────────────────────────────────────────


class TestGetTopNewsTool:
    """Teste le function tool get_top_news."""

    @pytest.fixture
    def mock_api(self):
        api = MagicMock()
        api.top_news.return_value = _make_top_news_response(3)
        return api

    @pytest.mark.asyncio
    async def test_returns_non_empty_string(self, mock_api):
        with patch("core.agent.tools.get_news_api", return_value=mock_api):
            from core.agent.tools import get_top_news
            result = await get_top_news.on_invoke_tool(
                _make_run_ctx(), '{"source_country":"fr","language":"fr"}'
            )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_result_contains_cluster_titles(self, mock_api):
        with patch("core.agent.tools.get_news_api", return_value=mock_api):
            from core.agent.tools import get_top_news
            result = await get_top_news.on_invoke_tool(
                _make_run_ctx(), '{"source_country":"fr","language":"fr"}'
            )
        assert "Titre cluster 1" in result

    @pytest.mark.asyncio
    async def test_calls_api_with_correct_country_and_language(self, mock_api):
        with patch("core.agent.tools.get_news_api", return_value=mock_api):
            from core.agent.tools import get_top_news
            await get_top_news.on_invoke_tool(
                _make_run_ctx(), '{"source_country":"us","language":"en"}'
            )
        kwargs = mock_api.top_news.call_args.kwargs
        assert kwargs.get("source_country") == "us"
        assert kwargs.get("language") == "en"

    @pytest.mark.asyncio
    async def test_uses_today_when_no_date_provided(self, mock_api):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with patch("core.agent.tools.get_news_api", return_value=mock_api):
            from core.agent.tools import get_top_news
            await get_top_news.on_invoke_tool(
                _make_run_ctx(), '{"source_country":"fr","language":"fr"}'
            )
        assert mock_api.top_news.call_args.kwargs.get("var_date") == today

    @pytest.mark.asyncio
    async def test_uses_provided_date(self, mock_api):
        with patch("core.agent.tools.get_news_api", return_value=mock_api):
            from core.agent.tools import get_top_news
            await get_top_news.on_invoke_tool(
                _make_run_ctx(), '{"source_country":"fr","language":"fr","date":"2026-05-04"}'
            )
        assert mock_api.top_news.call_args.kwargs.get("var_date") == "2026-05-04"

    @pytest.mark.asyncio
    async def test_empty_response_returns_no_news_message(self):
        empty_api = MagicMock()
        empty_api.top_news.return_value = TopNews200Response(
            top_news=[], language="fr", country="fr"
        )
        with patch("core.agent.tools.get_news_api", return_value=empty_api):
            from core.agent.tools import get_top_news
            result = await get_top_news.on_invoke_tool(
                _make_run_ctx(), '{"source_country":"fr","language":"fr"}'
            )
        assert "Aucune actualité" in result

    @pytest.mark.asyncio
    async def test_result_contains_source_url(self, mock_api):
        with patch("core.agent.tools.get_news_api", return_value=mock_api):
            from core.agent.tools import get_top_news
            result = await get_top_news.on_invoke_tool(
                _make_run_ctx(), '{"source_country":"fr","language":"fr"}'
            )
        assert "https://example.com" in result

    @pytest.mark.asyncio
    async def test_result_contains_date_header(self, mock_api):
        with patch("core.agent.tools.get_news_api", return_value=mock_api):
            from core.agent.tools import get_top_news
            result = await get_top_news.on_invoke_tool(
                _make_run_ctx(), '{"source_country":"fr","language":"fr","date":"2026-06-05"}'
            )
        assert "2026-06-05" in result


# ── Tests search_news tool (smoke) ────────────────────────────────────────────


class TestSearchNewsTool:
    """Smoke tests pour search_news tool."""

    @pytest.mark.asyncio
    async def test_returns_string_on_results(self):
        from core.news.search import SearchArticle

        mock_articles = [
            SearchArticle(
                title="IA en France",
                url="https://example.com/ia",
                summary="Résumé IA.",
                publish_date="2026-06-05 08:00:00",
            )
        ]
        with patch("core.agent.tools._search_news", return_value=mock_articles):
            from core.agent.tools import search_news

            result = await search_news.on_invoke_tool(
                _make_run_ctx(),
                '{"query":"intelligence artificielle","language":"fr","max_results":5}',
            )
        assert isinstance(result, str)
        assert "IA en France" in result

    @pytest.mark.asyncio
    async def test_returns_no_result_message_when_empty(self):
        with patch("core.agent.tools._search_news", return_value=[]):
            from core.agent.tools import search_news

            result = await search_news.on_invoke_tool(
                _make_run_ctx(),
                '{"query":"sujetintrouvable","language":"fr","max_results":5}',
            )
        assert "Aucun article" in result
