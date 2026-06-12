"""
Tests for core.worldnewsapi.worldnews
--------------------------------------
Unit tests  : mockent l'api_client, aucun appel réseau.
Integration : marqués `integration`, appellent l'API réelle (nécessite
              WORLDNEWSAPI_KEY dans .env).

Inspiration : https://github.com/ddsky/world-news-api-clients/tree/main/python/test
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── path setup (identique aux autres tests du projet) ─────────────────────────
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
from worldnewsapi.models.search_news200_response import SearchNews200Response
from worldnewsapi.models.search_news200_response_news_inner import (
    SearchNews200ResponseNewsInner,
)

from core.worldnewsapi.worldnews import NewsApi, get_news_api


# ── helpers ───────────────────────────────────────────────────────────────────


def _make_api_with_mock_client() -> tuple[NewsApi, MagicMock]:
    """Retourne (NewsApi, mock_api_client)."""
    mock_client = MagicMock()
    api = NewsApi(api_client=mock_client)
    return api, mock_client


def _fake_top_news_response() -> TopNews200Response:
    article = TopNews200ResponseTopNewsInnerNewsInner(
        id=1,
        title="Titre de test",
        url="https://example.com/news/1",
        publish_date="2026-06-01 10:00:00",
        authors=["Auteur Test"],
        summary="Un résumé.",
        text="Le texte complet de l'article de test.",
        image="https://example.com/img.jpg",
        author="Auteur Test",
    )
    cluster = TopNews200ResponseTopNewsInner(news=[article])
    return TopNews200Response(top_news=[cluster], language="fr", country="fr")


# ── Unit tests — sérialisation ────────────────────────────────────────────────


class TestTopNewsSerialize:
    """Vérifie que _top_news_serialize produit les bons query params."""

    def setup_method(self):
        self.api, self.mock_client = _make_api_with_mock_client()
        self.mock_client.param_serialize.return_value = (
            "GET",
            "/top-news",
            {},
            [],
            {},
            None,
            [],
            {},
            [],
        )

    def test_required_params_are_in_query(self):
        self.api._top_news_serialize(
            source_country="fr",
            language="fr",
            var_date=None,
            headlines_only=None,
            _request_auth=None,
            _content_type=None,
            _headers=None,
            _host_index=0,
        )
        call_kwargs = self.mock_client.param_serialize.call_args
        query_params = call_kwargs.kwargs["query_params"]
        keys = [k for k, _ in query_params]
        assert "source-country" in keys
        assert "language" in keys

    def test_optional_date_added_when_provided(self):
        self.api._top_news_serialize(
            source_country="fr",
            language="fr",
            var_date="2026-06-01",
            headlines_only=None,
            _request_auth=None,
            _content_type=None,
            _headers=None,
            _host_index=0,
        )
        call_kwargs = self.mock_client.param_serialize.call_args
        query_params = call_kwargs.kwargs["query_params"]
        assert ("date", "2026-06-01") in query_params

    def test_headlines_only_added_when_provided(self):
        self.api._top_news_serialize(
            source_country="us",
            language="en",
            var_date=None,
            headlines_only=True,
            _request_auth=None,
            _content_type=None,
            _headers=None,
            _host_index=0,
        )
        call_kwargs = self.mock_client.param_serialize.call_args
        query_params = call_kwargs.kwargs["query_params"]
        assert ("headlines-only", True) in query_params

    def test_optional_params_absent_when_none(self):
        self.api._top_news_serialize(
            source_country="fr",
            language="fr",
            var_date=None,
            headlines_only=None,
            _request_auth=None,
            _content_type=None,
            _headers=None,
            _host_index=0,
        )
        call_kwargs = self.mock_client.param_serialize.call_args
        query_params = call_kwargs.kwargs["query_params"]
        keys = [k for k, _ in query_params]
        assert "date" not in keys
        assert "headlines-only" not in keys

    def test_auth_settings_contain_both_schemes(self):
        self.api._top_news_serialize(
            source_country="fr",
            language="fr",
            var_date=None,
            headlines_only=None,
            _request_auth=None,
            _content_type=None,
            _headers=None,
            _host_index=0,
        )
        call_kwargs = self.mock_client.param_serialize.call_args
        auth_settings = call_kwargs.kwargs["auth_settings"]
        assert "apiKey" in auth_settings
        assert "headerApiKey" in auth_settings

    def test_resource_path_is_top_news(self):
        self.api._top_news_serialize(
            source_country="fr",
            language="fr",
            var_date=None,
            headlines_only=None,
            _request_auth=None,
            _content_type=None,
            _headers=None,
            _host_index=0,
        )
        call_kwargs = self.mock_client.param_serialize.call_args
        assert call_kwargs.kwargs["resource_path"] == "/top-news"
        assert call_kwargs.kwargs["method"] == "GET"


# ── Unit tests — top_news (flux complet mocké) ────────────────────────────────


class TestTopNews:
    """Vérifie le comportement de top_news avec api_client mocké."""

    def setup_method(self):
        self.api, self.mock_client = _make_api_with_mock_client()

        # _top_news_serialize doit renvoyer un tuple dépaquetable
        self.mock_client.param_serialize.return_value = (
            "GET",
            "/top-news",
            {},
            [],
            {},
            None,
            [],
            {},
            [],
        )

        fake_response = _fake_top_news_response()
        mock_response_data = MagicMock()
        mock_response_data.read.return_value = None
        self.mock_client.call_api.return_value = mock_response_data

        mock_deserialized = MagicMock()
        mock_deserialized.data = fake_response
        self.mock_client.response_deserialize.return_value = mock_deserialized

        self.fake_response = fake_response

    def test_returns_top_news_200_response(self):
        result = self.api.top_news(source_country="fr", language="fr")
        assert isinstance(result, TopNews200Response)

    def test_result_contains_top_news_list(self):
        result = self.api.top_news(source_country="fr", language="fr")
        assert result.top_news is not None
        assert len(result.top_news) == 1

    def test_result_cluster_contains_articles(self):
        result = self.api.top_news(source_country="fr", language="fr")
        cluster = result.top_news[0]
        assert len(cluster.news) == 1
        assert cluster.news[0].title == "Titre de test"

    def test_call_api_is_called_once(self):
        self.api.top_news(source_country="fr", language="fr")
        self.mock_client.call_api.assert_called_once()

    def test_response_read_is_called(self):
        self.api.top_news(source_country="fr", language="fr")
        self.mock_client.call_api.return_value.read.assert_called_once()

    def test_with_date_and_headlines_only(self):
        result = self.api.top_news(
            source_country="us",
            language="en",
            var_date="2026-06-01",
            headlines_only=True,
        )
        assert isinstance(result, TopNews200Response)


# ── Unit tests — validation pydantic ─────────────────────────────────────────


class TestTopNewsValidation:
    """Vérifie que les contraintes Pydantic sont appliquées."""

    def setup_method(self):
        self.api, _ = _make_api_with_mock_client()

    def test_country_code_too_long_raises(self):
        from pydantic import ValidationError

        with pytest.raises((ValidationError, Exception)):
            self.api.top_news(source_country="fra", language="fr")

    def test_language_code_too_long_raises(self):
        from pydantic import ValidationError

        with pytest.raises((ValidationError, Exception)):
            self.api.top_news(source_country="fr", language="fra")


def _fake_search_news_response(n: int = 2) -> SearchNews200Response:
    articles = [
        SearchNews200ResponseNewsInner(
            id=i + 1,
            title=f"Article {i + 1}",
            url=f"https://example.com/news/{i + 1}",
            publish_date="2026-06-05 08:00:00",
            authors=["Journaliste Test"],
            summary=f"Résumé article {i + 1}.",
            text=f"Texte complet article {i + 1}.",
            language="fr",
            source_country="fr",
            category="technology",
            sentiment=0.1,
        )
        for i in range(n)
    ]
    return SearchNews200Response(offset=0, number=n, available=n, news=articles)


# ── Unit tests — search_news sérialisation ────────────────────────────────────


class TestSearchNewsSerialize:
    """Vérifie que _search_news_serialize produit les bons query params."""

    def setup_method(self):
        self.api, self.mock_client = _make_api_with_mock_client()
        self.mock_client.param_serialize.return_value = (
            "GET",
            "/search-news",
            {},
            [],
            {},
            None,
            [],
            {},
            [],
        )

    def test_text_query_is_in_params(self):
        self.api._search_news_serialize(
            text="intelligence artificielle",
            text_match_indexes=None,
            source_country=None,
            language="fr",
            min_sentiment=None,
            max_sentiment=None,
            earliest_publish_date=None,
            latest_publish_date=None,
            news_sources=None,
            authors=None,
            categories=None,
            entities=None,
            location_filter=None,
            sort=None,
            sort_direction=None,
            offset=None,
            number=None,
            _request_auth=None,
            _content_type=None,
            _headers=None,
            _host_index=0,
        )
        query_params = self.mock_client.param_serialize.call_args.kwargs["query_params"]
        keys = [k for k, _ in query_params]
        assert "text" in keys
        assert ("text", "intelligence artificielle") in query_params

    def test_language_is_in_params(self):
        self.api._search_news_serialize(
            text="test",
            text_match_indexes=None,
            source_country=None,
            language="fr",
            min_sentiment=None,
            max_sentiment=None,
            earliest_publish_date=None,
            latest_publish_date=None,
            news_sources=None,
            authors=None,
            categories=None,
            entities=None,
            location_filter=None,
            sort=None,
            sort_direction=None,
            offset=None,
            number=None,
            _request_auth=None,
            _content_type=None,
            _headers=None,
            _host_index=0,
        )
        query_params = self.mock_client.param_serialize.call_args.kwargs["query_params"]
        assert ("language", "fr") in query_params

    def test_number_is_in_params_when_set(self):
        self.api._search_news_serialize(
            text="test",
            text_match_indexes=None,
            source_country=None,
            language=None,
            min_sentiment=None,
            max_sentiment=None,
            earliest_publish_date=None,
            latest_publish_date=None,
            news_sources=None,
            authors=None,
            categories=None,
            entities=None,
            location_filter=None,
            sort=None,
            sort_direction=None,
            offset=None,
            number=10,
            _request_auth=None,
            _content_type=None,
            _headers=None,
            _host_index=0,
        )
        query_params = self.mock_client.param_serialize.call_args.kwargs["query_params"]
        assert ("number", 10) in query_params

    def test_optional_params_absent_when_none(self):
        self.api._search_news_serialize(
            text="test",
            text_match_indexes=None,
            source_country=None,
            language=None,
            min_sentiment=None,
            max_sentiment=None,
            earliest_publish_date=None,
            latest_publish_date=None,
            news_sources=None,
            authors=None,
            categories=None,
            entities=None,
            location_filter=None,
            sort=None,
            sort_direction=None,
            offset=None,
            number=None,
            _request_auth=None,
            _content_type=None,
            _headers=None,
            _host_index=0,
        )
        query_params = self.mock_client.param_serialize.call_args.kwargs["query_params"]
        keys = [k for k, _ in query_params]
        assert "language" not in keys
        assert "number" not in keys
        assert "source-country" not in keys

    def test_resource_path_is_search_news(self):
        self.api._search_news_serialize(
            text="test",
            text_match_indexes=None,
            source_country=None,
            language=None,
            min_sentiment=None,
            max_sentiment=None,
            earliest_publish_date=None,
            latest_publish_date=None,
            news_sources=None,
            authors=None,
            categories=None,
            entities=None,
            location_filter=None,
            sort=None,
            sort_direction=None,
            offset=None,
            number=None,
            _request_auth=None,
            _content_type=None,
            _headers=None,
            _host_index=0,
        )
        call_kwargs = self.mock_client.param_serialize.call_args.kwargs
        assert call_kwargs["resource_path"] == "/search-news"
        assert call_kwargs["method"] == "GET"

    def test_auth_settings_contain_both_schemes(self):
        self.api._search_news_serialize(
            text="test",
            text_match_indexes=None,
            source_country=None,
            language=None,
            min_sentiment=None,
            max_sentiment=None,
            earliest_publish_date=None,
            latest_publish_date=None,
            news_sources=None,
            authors=None,
            categories=None,
            entities=None,
            location_filter=None,
            sort=None,
            sort_direction=None,
            offset=None,
            number=None,
            _request_auth=None,
            _content_type=None,
            _headers=None,
            _host_index=0,
        )
        auth_settings = self.mock_client.param_serialize.call_args.kwargs[
            "auth_settings"
        ]
        assert "apiKey" in auth_settings
        assert "headerApiKey" in auth_settings


# ── Unit tests — search_news (flux complet mocké) ─────────────────────────────


class TestSearchNews:
    """Vérifie le comportement de search_news avec api_client mocké."""

    def setup_method(self):
        self.api, self.mock_client = _make_api_with_mock_client()
        self.mock_client.param_serialize.return_value = (
            "GET",
            "/search-news",
            {},
            [],
            {},
            None,
            [],
            {},
            [],
        )

        fake_response = _fake_search_news_response(2)
        mock_response_data = MagicMock()
        mock_response_data.read.return_value = None
        self.mock_client.call_api.return_value = mock_response_data

        mock_deserialized = MagicMock()
        mock_deserialized.data = fake_response
        self.mock_client.response_deserialize.return_value = mock_deserialized

        self.fake_response = fake_response

    def test_returns_search_news_200_response(self):
        result = self.api.search_news(text="intelligence artificielle", language="fr")
        assert isinstance(result, SearchNews200Response)

    def test_result_contains_news_list(self):
        result = self.api.search_news(text="IA", language="fr")
        assert result.news is not None
        assert len(result.news) == 2

    def test_result_articles_have_title(self):
        result = self.api.search_news(text="IA", language="fr")
        assert result.news[0].title == "Article 1"
        assert result.news[1].title == "Article 2"

    def test_call_api_is_called_once(self):
        self.api.search_news(text="IA", language="fr")
        self.mock_client.call_api.assert_called_once()

    def test_response_read_is_called(self):
        self.api.search_news(text="IA", language="fr")
        self.mock_client.call_api.return_value.read.assert_called_once()

    def test_with_number_param(self):
        result = self.api.search_news(text="élection", language="fr", number=5)
        assert isinstance(result, SearchNews200Response)

    def test_empty_result_returns_empty_news_list(self):
        empty_response = SearchNews200Response(offset=0, number=0, available=0, news=[])
        mock_deser = MagicMock()
        mock_deser.data = empty_response
        self.mock_client.response_deserialize.return_value = mock_deser

        result = self.api.search_news(text="sujetinexistant123xyz", language="fr")
        assert result.news == []


# ── Unit tests — get_news_api ─────────────────────────────────────────────────


class TestGetNewsApi:
    """Vérifie que get_news_api configure correctement l'ApiClient."""

    def test_returns_news_api_instance(self):
        with (
            patch("core.config.WORLDNEWSAPI_KEY", "fake-key-for-test"),
            patch("core.config.WORLDNEWS_MOCK", False),
        ):
            api = get_news_api()
        assert isinstance(api, NewsApi)

    def test_api_key_is_set_in_configuration(self):
        with (
            patch("core.config.WORLDNEWSAPI_KEY", "my-secret-key"),
            patch("core.config.WORLDNEWS_MOCK", False),
        ):
            api = get_news_api()
        config = api.api_client.configuration
        assert config.api_key.get("apiKey") == "my-secret-key"
        assert config.api_key.get("headerApiKey") == "my-secret-key"

    def test_host_is_worldnewsapi(self):
        with (
            patch("core.config.WORLDNEWSAPI_KEY", "fake-key-for-test"),
            patch("core.config.WORLDNEWS_MOCK", False),
        ):
            api = get_news_api()
        assert "worldnewsapi.com" in api.api_client.configuration.host


# ── Integration tests — appel API réel ───────────────────────────────────────

WORLDNEWSAPI_KEY = os.getenv("WORLDNEWSAPI_KEY", "")

pytestmark_integration = pytest.mark.skipif(
    not WORLDNEWSAPI_KEY,
    reason="WORLDNEWSAPI_KEY absent — test d'intégration ignoré",
)


@pytestmark_integration
class TestTopNewsIntegration:
    """Appels réels à l'API WorldNews (nécessitent WORLDNEWSAPI_KEY)."""

    def setup_method(self):
        self.api = get_news_api()

    def test_top_news_france_returns_response(self):
        result = self.api.top_news(source_country="fr", language="fr")
        assert isinstance(result, TopNews200Response)
        assert result.top_news is not None

    def test_top_news_france_has_articles(self):
        result = self.api.top_news(source_country="fr", language="fr")
        total_articles = sum(len(c.news) for c in result.top_news)
        assert total_articles > 0

    def test_top_news_headlines_only(self):
        result = self.api.top_news(
            source_country="fr", language="fr", headlines_only=True
        )
        assert isinstance(result, TopNews200Response)

    def test_top_news_us_english(self):
        result = self.api.top_news(source_country="us", language="en")
        assert isinstance(result, TopNews200Response)
        assert result.top_news is not None

    def test_top_news_with_date(self):
        result = self.api.top_news(
            source_country="fr", language="fr", var_date="2026-05-30"
        )
        assert isinstance(result, TopNews200Response)

    def test_top_news_articles_have_required_fields(self):
        result = self.api.top_news(
            source_country="fr", language="fr", headlines_only=True
        )
        for cluster in result.top_news:
            for article in cluster.news:
                assert article.id is not None
                assert article.title is not None
                assert article.url is not None


@pytestmark_integration
class TestSearchNewsIntegration:
    """Appels réels à l'API WorldNews — search_news (nécessitent WORLDNEWSAPI_KEY)."""

    def setup_method(self):
        self.api = get_news_api()

    def test_search_news_returns_response(self):
        result = self.api.search_news(text="intelligence artificielle", language="fr")
        assert isinstance(result, SearchNews200Response)

    def test_search_news_has_articles(self):
        result = self.api.search_news(text="économie", language="fr", number=5)
        assert result.news is not None
        assert len(result.news) > 0

    def test_search_news_articles_have_required_fields(self):
        result = self.api.search_news(text="technologie", language="fr", number=3)
        for article in result.news:
            assert article.id is not None
            assert article.title is not None
            assert article.url is not None

    def test_search_news_empty_result(self):
        result = self.api.search_news(text="xyzzy123notexist456abc", language="fr")
        assert isinstance(result, SearchNews200Response)
        assert result.news is not None
