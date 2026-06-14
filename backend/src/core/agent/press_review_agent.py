"""Agent spécialisé pour la génération de revue de presse.

Contrairement à search_agent.py, cet agent n'a pas d'outils et utilise
`output_type` pour produire une sortie structurée directement exploitable
par la couche de persistance.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from agents import Agent, ModelSettings, OpenAIChatCompletionsModel

from core.config import AGENT_MAX_TOKENS, LLM_MODEL
from core.llm_client import build_llm_client


class ArticleSummary(BaseModel):
    """Un article mentionné dans la revue de presse."""

    title: str = Field(description="Titre de l'article mentionné dans la conversation")
    summary: str = Field(description="Résumé concis de l'article (2-3 phrases)")
    source: str | None = Field(
        default=None,
        description=(
            "Full URL of the article (e.g. https://lemonde.fr/...). "
            "ALWAYS use the URL, never the publication name alone. "
            "Leave null only if no URL is available in the conversation or context."
        ),
    )


class PressReviewOutput(BaseModel):
    """Sortie structurée de la revue de presse."""

    title: str = Field(description="Titre informatif et concis pour la revue de presse")
    summary: str = Field(
        description="Synthèse générale de la revue de presse (3-5 phrases)"
    )
    articles: list[ArticleSummary] = Field(
        description="Liste des articles identifiés dans la conversation avec leur résumé"
    )


def _build_instructions(ctx, agent) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return (
        "You are NewsFoundry, an AI assistant specialized in press review analysis.\n\n"
        f"Today's date is: {today}.\n\n"
        "Your task is to synthesize the provided chat conversation into a structured "
        "press review. Identify the key articles and topics discussed, extract factual "
        "information, and organize them into a coherent review with a title, general "
        "summary, and individual article summaries.\n\n"
        "IMPORTANT: For each article's 'source' field, you MUST use the full URL "
        "(e.g. https://...) found in the conversation or context. Never use a "
        "publication name as the source — always use the URL. If no URL is available "
        "for a specific article, leave 'source' as null.\n\n"
        "If the conversation does not contain any article or news discussion, generate "
        "a review based on the main topics discussed, with a single article entry "
        "summarizing the key exchange."
    )


_openai_client = build_llm_client()

press_review_agent = Agent[None](
    name="newsfoundry_press_review_agent",
    instructions=_build_instructions,
    tools=[],
    output_type=PressReviewOutput,
    model=OpenAIChatCompletionsModel(
        model=LLM_MODEL,
        openai_client=_openai_client,
    ),
    model_settings=ModelSettings(
        temperature=0.3,
        max_tokens=AGENT_MAX_TOKENS,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    ),
)
