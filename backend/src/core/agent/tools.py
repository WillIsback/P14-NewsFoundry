"""Function tools exposés à l'agent de chat NewsFoundry.

Chaque tool est une coroutine décorée avec `@function_tool`.
Son type-hint et sa docstring constituent le schéma JSON envoyé au LLM.

Règle de routing (résumée dans les docstrings) :
- `get_top_news` → actualités générales du jour / d'une date précise
- `search_news`  → approfondissement d'un sujet ou d'un thème précis

Les outputs sont en Markdown pour être directement lisibles par le LLM.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from agents import function_tool

from core.news.search import search_news as _search_news
from core.worldnewsapi.worldnews import get_news_api


@function_tool
async def get_top_news(
    source_country: str = "fr",
    language: str = "fr",
    date: str | None = None,
) -> str:
    """Get the top news headlines clustered from multiple sources for a country.

    Use this tool when the user asks for general daily news, top headlines,
    or 'what's happening today/this week' type of questions — with NO specific topic.
    Also use it when the user asks for news of a SPECIFIC PAST DATE.
    Do NOT use this for specific topic searches — use `search_news` instead.

    Args:
        source_country: ISO 3166-1 alpha-2 country code (default: "fr").
        language: ISO 639-1 language code (default: "fr").
        date: Date in YYYY-MM-DD format. Defaults to today if not provided.
              Use this when the user explicitly asks about a specific date.

    Returns:
        A Markdown-formatted list of top news clusters with titles and sources.
    """
    from core.news.reducer import reduce_clusters

    api = get_news_api()
    effective_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    response = await asyncio.to_thread(
        api.top_news,
        source_country=source_country,
        language=language,
        var_date=effective_date,
    )

    clusters = reduce_clusters(response, top_n=10)

    if not clusters:
        return f"Aucune actualité trouvée pour le {effective_date}."

    lines: list[str] = [f"## Top actualités — {effective_date}\n"]
    for i, cluster in enumerate(clusters, 1):
        title = cluster.titles[0] if cluster.titles else "Sans titre"
        summary = cluster.summaries[0] if cluster.summaries else ""
        summary_str = f"\n> {summary}" if summary else ""
        lines.append(
            f"**{i}. {title}** ({cluster.article_count} articles){summary_str}\n"
            f"Source : {cluster.top_url}\n"
        )

    return "\n---\n".join(lines)


@function_tool
async def search_news(
    query: str,
    language: str = "fr",
    max_results: int = 10,
) -> str:
    """Search for recent news articles on a specific topic.

    Use this tool when the user wants to explore a specific subject in depth
    (e.g. "tell me more about the Iran conflict", "what's happening with AI in France").
    Do NOT use this for general 'what's the news today' requests — use `get_top_news` instead.

    Args:
        query: Keywords or topic to search for (e.g. "conflit Iran", "IA France").
               Use the same language as the `language` parameter.
        language: ISO 639-1 language code for the articles (default: "fr").
        max_results: Number of articles to return, between 1 and 20 (default: 10).

    Returns:
        A Markdown-formatted list of articles with title, summary, date, and URL.
        Returns a message indicating no results if nothing was found.
    """
    articles = await _search_news(
        query=query, language=language, max_results=max_results
    )

    if not articles:
        return f"Aucun article trouvé pour la recherche : « {query} »."

    lines: list[str] = [f"## Résultats de recherche pour « {query} »\n"]
    for i, article in enumerate(articles, 1):
        date_str = f" — {article.publish_date}" if article.publish_date else ""
        summary_str = f"\n> {article.summary}" if article.summary else ""
        lines.append(
            f"**{i}. {article.title}**{date_str}{summary_str}\nSource : {article.url}\n"
        )

    return "\n---\n".join(lines)
