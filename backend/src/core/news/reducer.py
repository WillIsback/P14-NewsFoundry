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
    article_count: int
    top_url: str


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
        top_url = articles[0].url or "" if articles else ""
        result.append(
            ClusterInput(
                cluster_index=idx,
                titles=titles,
                summaries=summaries,
                article_count=len(articles),
                top_url=top_url,
            )
        )
    return result
