"""Agent spécialisé pour la génération de revue de presse.

Contrairement à search_agent.py, cet agent n'a pas d'outils et utilise
`output_type` pour produire une sortie structurée directement exploitable
par la couche de persistance.
"""

from __future__ import annotations

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
        description="URL source ou nom de la publication si mentionné dans la conversation",
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


_instructions = (
    "You are NewsFoundry, an AI assistant specialized in press review analysis.\n\n"
    "Your task is to synthesize the provided chat conversation into a structured "
    "press review. Identify the key articles and topics discussed, extract factual "
    "information, and organize them into a coherent review with a title, general "
    "summary, and individual article summaries. Be factual and cite sources when "
    "they are mentioned in the conversation.\n\n"
    "If the conversation does not contain any article or news discussion, generate "
    "a review based on the main topics discussed, with a single article entry "
    "summarizing the key exchange."
)

_openai_client = build_llm_client()

press_review_agent = Agent[None](
    name="newsfoundry_press_review_agent",
    instructions=_instructions,
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
