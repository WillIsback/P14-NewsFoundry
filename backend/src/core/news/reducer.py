"""ClusterReducer — transforme la réponse WorldNewsAPI en inputs exploitables.

Trie les clusters par taille décroissante, prend les top_n premiers,
et extrait titres + summaries pour chaque cluster.
"""

from dataclasses import dataclass

from worldnewsapi.models.top_news200_response import TopNews200Response


@dataclass
class ClusterInput:
    cluster_index: int
    titles: list[str]
    summaries: list[str]
    texts: list[str]
    article_count: int
    top_url: str
    publish_date: str
    authors: list[str]
    category: str


def reduce_clusters(
    response: TopNews200Response, top_n: int = 25
) -> list[ClusterInput]:
    """Trie les clusters par taille décroissante, prend top_n, extrait titres + summaries.

    Args:
        response: Réponse brute de l'API WorldNews.
        top_n: Nombre maximum de clusters à conserver.

    Returns:
        Liste de ClusterInput triée du plus grand au plus petit cluster.
    """
    clusters = response.top_news or []
    sorted_clusters = sorted(clusters, key=lambda c: len(c.news or []), reverse=True)

    result: list[ClusterInput] = []
    for idx, cluster in enumerate(sorted_clusters[:top_n]):
        articles = cluster.news or []
        titles = [a.title for a in articles if a.title]
        summaries = [a.summary for a in articles if a.summary]
        texts = [a.text for a in articles if a.text]
        top_article = articles[0] if articles else None
        top_url = top_article.url or "" if top_article else ""
        publish_date = top_article.publish_date or "" if top_article else ""
        authors = top_article.authors or [] if top_article else []
        category = getattr(top_article, "category", None) or "" if top_article else ""
        result.append(
            ClusterInput(
                cluster_index=idx,
                titles=titles,
                summaries=summaries,
                texts=texts,
                article_count=len(articles),
                top_url=top_url,
                publish_date=publish_date,
                authors=authors,
                category=category,
            )
        )
    return result
