"""Tests TDD pour core.news.reducer.reduce_clusters.

Phase RED : ces tests doivent échouer avant que le code soit écrit.
"""

from pathlib import Path
import sys


BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from worldnewsapi.models.top_news200_response import TopNews200Response
from worldnewsapi.models.top_news200_response_top_news_inner import (
    TopNews200ResponseTopNewsInner,
)
from worldnewsapi.models.top_news200_response_top_news_inner_news_inner import (
    TopNews200ResponseTopNewsInnerNewsInner,
)

from core.news.reducer import reduce_clusters


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_article(
    title: str | None = "Titre",
    url: str = "http://example.com",
    summary: str | None = "Résumé",
) -> TopNews200ResponseTopNewsInnerNewsInner:
    return TopNews200ResponseTopNewsInnerNewsInner(
        id=1,
        title=title,
        url=url,
        summary=summary,
        publish_date="2026-06-01 10:00:00",
        authors=[],
        text="",
        image=None,
        author=None,
    )


def _make_cluster(article_count: int = 3) -> TopNews200ResponseTopNewsInner:
    articles = [
        _make_article(title=f"Titre {i}", url=f"http://example.com/{i}")
        for i in range(article_count)
    ]
    return TopNews200ResponseTopNewsInner(news=articles)


def _make_response(cluster_sizes: list[int]) -> TopNews200Response:
    clusters = [_make_cluster(n) for n in cluster_sizes]
    return TopNews200Response(top_news=clusters, language="fr", country="fr")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_reduce_clusters_returns_top_25_from_30():
    """Avec 30 clusters, reduce_clusters retourne exactement 25."""
    response = _make_response([1] * 30)
    result = reduce_clusters(response, top_n=25)
    assert len(result) == 25


def test_reduce_clusters_sorted_descending():
    """Les clusters sont triés par taille décroissante."""
    # Tailles dans un ordre quelconque
    sizes = [3, 1, 5, 2, 4]
    response = _make_response(sizes)
    result = reduce_clusters(response, top_n=5)
    counts = [r.article_count for r in result]
    assert counts == sorted(counts, reverse=True)


def test_reduce_clusters_largest_first():
    """Le premier cluster résultant est le plus grand."""
    response = _make_response([2, 10, 5])
    result = reduce_clusters(response, top_n=3)
    assert result[0].article_count == 10


def test_titles_correctly_extracted():
    """Les titres des articles sont correctement extraits dans le ClusterInput."""
    cluster = TopNews200ResponseTopNewsInner(
        news=[
            _make_article(title="Alpha", url="http://a.com"),
            _make_article(title="Beta", url="http://b.com"),
        ]
    )
    response = TopNews200Response(top_news=[cluster], language="fr", country="fr")
    result = reduce_clusters(response, top_n=1)
    assert "Alpha" in result[0].titles
    assert "Beta" in result[0].titles


def test_summaries_correctly_extracted():
    """Les summaries des articles sont correctement extraits."""
    cluster = TopNews200ResponseTopNewsInner(
        news=[
            TopNews200ResponseTopNewsInnerNewsInner(
                id=1,
                title="T1",
                url="http://x.com",
                summary="Résumé A",
                publish_date="2026-06-01 10:00:00",
                authors=[],
                text="",
                image=None,
                author=None,
            ),
        ]
    )
    response = TopNews200Response(top_news=[cluster], language="fr", country="fr")
    result = reduce_clusters(response, top_n=1)
    assert "Résumé A" in result[0].summaries


def test_articles_without_title_ignored():
    """Les articles sans titre ne doivent pas apparaître dans les titles."""
    cluster = TopNews200ResponseTopNewsInner(
        news=[
            _make_article(title=None, url="http://a.com"),
            _make_article(title="Valide", url="http://b.com"),
        ]
    )
    response = TopNews200Response(top_news=[cluster], language="fr", country="fr")
    result = reduce_clusters(response, top_n=1)
    assert None not in result[0].titles
    assert "Valide" in result[0].titles


def test_articles_without_summary_ignored():
    """Les articles sans summary ne doivent pas apparaître dans les summaries."""
    cluster = TopNews200ResponseTopNewsInner(
        news=[
            _make_article(title="T1", url="http://a.com", summary=None),
            _make_article(title="T2", url="http://b.com", summary="Ok"),
        ]
    )
    response = TopNews200Response(top_news=[cluster], language="fr", country="fr")
    result = reduce_clusters(response, top_n=1)
    assert None not in result[0].summaries
    assert "Ok" in result[0].summaries


def test_top_url_is_first_article_url():
    """top_url est l'URL du premier article du cluster (après tri)."""
    cluster = TopNews200ResponseTopNewsInner(
        news=[
            _make_article(title="Premier", url="http://first.com"),
            _make_article(title="Deuxième", url="http://second.com"),
        ]
    )
    response = TopNews200Response(top_news=[cluster], language="fr", country="fr")
    result = reduce_clusters(response, top_n=1)
    assert result[0].top_url == "http://first.com"


def test_empty_response_returns_empty_list():
    """Avec top_news=None, retourne une liste vide sans crash."""
    response = TopNews200Response(top_news=None, language="fr", country="fr")
    result = reduce_clusters(response)
    assert result == []


def test_fewer_clusters_than_top_n_returns_all():
    """Avec moins de top_n clusters, retourne tous les clusters."""
    response = _make_response([1, 2, 3])
    result = reduce_clusters(response, top_n=10)
    assert len(result) == 3


def test_cluster_index_matches_sorted_order():
    """L'index de chaque ClusterInput correspond à sa position après tri."""
    response = _make_response([1, 5, 2])
    result = reduce_clusters(response, top_n=3)
    for i, r in enumerate(result):
        assert r.cluster_index == i


def test_article_count_matches_cluster_size():
    """article_count correspond au nombre réel d'articles dans le cluster."""
    response = _make_response([7, 3, 5])
    result = reduce_clusters(response, top_n=3)
    # Trié décroissant : 7, 5, 3
    assert result[0].article_count == 7
    assert result[1].article_count == 5
    assert result[2].article_count == 3
