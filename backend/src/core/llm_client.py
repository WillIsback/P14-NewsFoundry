from __future__ import annotations

from openai import AsyncOpenAI
from core.config import LLM_API_KEY, LLM_BASE_URL


def build_llm_client(*args, **kwargs) -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
    )
