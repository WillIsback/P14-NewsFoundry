"""Service de recherche d'articles via WorldNewsAPI.

Fournit `search_news`, une coroutine simple qui effectue un appel à
`/search-news` et retourne une liste de `SearchArticle` normalisés —
un format minimal et clair, optimisé pour la consommation par un LLM.
"""

from __future__ import annotations

import asyncio

from pydantic import BaseModel, Field

from core.worldnewsapi.worldnews import get_news_api


class SearchArticle(BaseModel):
    """Article normalisé retourné par la recherche.

    Champs volontairement réduits : seules les informations
    pertinentes pour un LLM sont exposées.
    """

    title: str
    url: str
    summary: str = Field(default="")
    publish_date: str = Field(default="")
    source_country: str = Field(default="")


async def search_news(
    query: str,
    language: str = "fr",
    max_results: int = 10,
) -> list[SearchArticle]:
    """Recherche des articles récents correspondant à `query`.

    Args:
        query: Mots-clés à rechercher (ex : « élection présidentielle »).
        language: Code ISO 639-1 de la langue cible (défaut : « fr »).
        max_results: Nombre maximum d'articles à retourner (plafonné à 20).

    Returns:
        Liste de `SearchArticle` triée du plus récent au plus ancien.
        Retourne une liste vide si aucun article n'est trouvé.
    """
    capped = min(max_results, 20)
    api = get_news_api()

    response = await asyncio.to_thread(
        api.search_news,
        text=query,
        language=language,
        number=capped,
        sort="publish-time",
        sort_direction="DESC",
        _request_timeout=(5, 25),  # (connect, read) — évite un hang qui bloque le run
    )

    articles = response.news or []
    return [
        SearchArticle(
            title=a.title or "",
            url=a.url or "",
            summary=a.summary or "",
            publish_date=a.publish_date or "",
            source_country=a.source_country or "",
        )
        for a in articles
        if a.title and a.url
    ]
