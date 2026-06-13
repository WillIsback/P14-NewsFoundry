from unittest.mock import MagicMock, patch

import core.llm_client as llm_client


def test_build_llm_client_uses_proxy_when_url_provided():
    with (
        patch.object(llm_client, "httpx") as mock_httpx,
        patch.object(llm_client, "AsyncOpenAI") as mock_openai,
    ):
        fake_http_client = MagicMock()
        mock_httpx.AsyncClient.return_value = fake_http_client

        llm_client.build_llm_client(proxy_url="http://localhost:1055")

        mock_httpx.AsyncClient.assert_called_once_with(proxy="http://localhost:1055")
        _, kwargs = mock_openai.call_args
        assert kwargs["http_client"] is fake_http_client


def test_build_llm_client_no_proxy_when_url_empty():
    with (
        patch.object(llm_client, "httpx") as mock_httpx,
        patch.object(llm_client, "AsyncOpenAI") as mock_openai,
    ):
        llm_client.build_llm_client(proxy_url=None)

        mock_httpx.AsyncClient.assert_not_called()
        _, kwargs = mock_openai.call_args
        assert kwargs["http_client"] is None


def test_build_llm_client_defaults_to_config_proxy():
    with (
        patch.object(llm_client, "LLM_PROXY_URL", "http://localhost:1055"),
        patch.object(llm_client, "httpx") as mock_httpx,
        patch.object(llm_client, "AsyncOpenAI") as mock_openai,
    ):
        fake_http_client = MagicMock()
        mock_httpx.AsyncClient.return_value = fake_http_client

        llm_client.build_llm_client()  # no arg → reads LLM_PROXY_URL

        mock_httpx.AsyncClient.assert_called_once_with(proxy="http://localhost:1055")
        _, kwargs = mock_openai.call_args
        assert kwargs["http_client"] is fake_http_client
