from unittest.mock import patch

import core.llm_client as llm_client


def test_build_llm_client():
    with (
        patch.object(llm_client, "LLM_API_KEY", "fake-secret-key"),
        patch.object(
            llm_client, "LLM_BASE_URL", "https://spark-787d-1.tail6cba9f.ts.net/v1"
        ),
        patch.object(llm_client, "AsyncOpenAI") as mock_openai,
    ):
        client = llm_client.build_llm_client()

        # Vérifie que le SDK OpenAI est initialisé avec la bonne URL et la bonne clé
        mock_openai.assert_called_once_with(
            api_key="fake-secret-key",
            base_url="https://spark-787d-1.tail6cba9f.ts.net/v1",
        )
        assert client == mock_openai.return_value
