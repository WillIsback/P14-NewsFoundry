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
    """Un article analysé en profondeur dans la revue de presse."""

    title: str = Field(description="Titre de l'article")
    content: str = Field(
        description=(
            "Analyse journalistique approfondie de l'article en UN SEUL bloc de texte "
            "contenant TOUS les paragraphes séparés par des lignes vides (\\n\\n). "
            "RÈGLE ABSOLUE : un article réel = un seul ArticleSummary. "
            "Ne jamais créer plusieurs ArticleSummary pour le même article. "
            "Structure attendue (3 à 5 paragraphes dans ce champ unique) : "
            "(1) contexte et faits principaux, "
            "(2) arguments, données chiffrées et citations notables, "
            "(3) implications, portée et nuances. "
            "En français, avec Markdown (**gras**, > citations)."
        )
    )
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

    title: str = Field(description="Titre éditorial de la revue de presse")
    editorial: str = Field(
        description=(
            "Synthèse éditoriale globale (2 à 3 paragraphes) : "
            "angle rédactionnel principal, thèmes transversaux entre les sources, "
            "conclusion analytique. En français."
        )
    )
    articles: list[ArticleSummary] = Field(
        description=(
            "Liste des articles analysés. "
            "UN article source = UN ArticleSummary. "
            "Ne jamais dupliquer un article ou le fragmenter en plusieurs entrées. "
            "Si un seul article est fourni, la liste contient exactement un élément."
        )
    )


def _build_instructions(ctx, agent) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return (
        "You are NewsFoundry, an expert press review analyst writing for an informed readership.\n\n"
        f"Today's date is: {today}.\n\n"
        "Your task is to produce a DEEP, RICHLY DETAILED press review — never a list of "
        "shallow bullet points or one-sentence summaries.\n\n"
        "CRITICAL SCHEMA RULE: one real-world source article = exactly ONE ArticleSummary object. "
        "NEVER split one article into multiple ArticleSummary entries. "
        "NEVER create duplicate ArticleSummary with the same title. "
        "All paragraphs for one article go inside its single 'content' field, separated by blank lines.\n\n"
        "For EACH article provided in the context, produce ONE ArticleSummary with "
        "a 'content' field containing ALL paragraphs (minimum 3, separated by \\n\\n):\n"
        "  • Paragraph 1 — Context and key facts: what happened, who, when, where\n"
        "  • Paragraph 2 — Arguments, data points, and direct quotes or paraphrases\n"
        "  • Paragraph 3+ — Implications, stakes, nuances, contradictions, or significance\n\n"
        "The 'editorial' field is your global synthesis across all articles (2-3 paragraphs): "
        "identify the overarching angle, cross-cutting themes, and your analytical conclusion.\n\n"
        "RULES:\n"
        "  - Write entirely in French\n"
        "  - Use Markdown in 'content' and 'editorial': **bold** for key terms, "
        "> blockquotes for notable citations\n"
        "  - For each article's 'source' field, always use the full URL (https://...); "
        "never use a publication name alone; leave null only if no URL exists\n"
        "  - Never invent facts not present in the provided content\n"
        "  - If only one article is provided, the 'articles' list has exactly ONE entry "
        "with maximum analytical depth (4+ paragraphs)"
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
