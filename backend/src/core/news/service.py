"""Service orchestrateur du pipeline d'ingestion de news.

Orchestre : appel WorldNewsAPI → réduction → labellisation LLM
→ construction système prompt → persistance en BDD.
"""

import asyncio
from datetime import datetime, timezone

from sqlmodel import Session

from core.news.labeler import label_clusters
from core.news.reducer import reduce_clusters
from core.prompts import build_news_system_prompt
from core.worldnewsapi.worldnews import get_news_api
from database.crud import create_top_news_context, get_top_news_context_by_chat
from database.models import TopNewsContext


async def fetch_and_build_context(
    chat_id: int,
    source_country: str,
    language: str,
    date: str | None,
    session: Session,
) -> TopNewsContext:
    """Orchestre le pipeline complet et persiste le résultat.

    Si un contexte existe déjà pour ce chat_id, le retourne directement
    sans aucun appel API ni LLM.

    Args:
        chat_id: Identifiant du chat cible.
        source_country: Code pays ISO 3166 (ex : "fr").
        language: Code langue ISO 6391 (ex : "fr").
        date: Date au format YYYY-MM-DD. Si None, utilise la date du jour UTC.
        session: Session SQLModel active.

    Returns:
        Le TopNewsContext créé ou existant.
    """
    existing = get_top_news_context_by_chat(session, chat_id)
    if existing:
        return existing

    effective_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 1. Appel synchrone dans thread pool pour ne pas bloquer la boucle asyncio
    api = get_news_api()
    response = await asyncio.to_thread(
        api.top_news,
        source_country=source_country,
        language=language,
        var_date=effective_date,
    )

    # 2. Réduction des clusters
    cluster_inputs = reduce_clusters(response, top_n=25)

    # 3. Labellisation par le LLM
    labeled = await label_clusters(cluster_inputs)

    # 4. Construction du system_prompt
    system_prompt = build_news_system_prompt(effective_date, labeled)

    # 5. Sérialisation pour la BDD
    news_items = [
        {
            "title": lc.cluster_title,
            "url": lc.top_url,
            "summary": lc.cluster_summary,
            "category": lc.category,
            "article_count": lc.article_count,
        }
        for lc in labeled
    ]

    # 6. Persistance
    return create_top_news_context(
        session=session,
        chat_id=chat_id,
        date=effective_date,
        source_country=source_country,
        language=language,
        system_prompt=system_prompt,
        news=news_items,
    )
