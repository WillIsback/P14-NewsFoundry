"""Tests TDD pour core.news.labeler.label_clusters.

Phase RED : ces tests doivent échouer avant que le code soit écrit.
"""

from pathlib import Path
import sys
from unittest.mock import AsyncMock, patch

import pytest

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from core.news.labeler import LabeledCluster, LabeledClusters, label_clusters
from core.news.reducer import ClusterInput

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_CATEGORY_VALUES = [
    "politics",
    "sports",
    "business",
    "technology",
    "entertainment",
    "health",
    "science",
    "lifestyle",
    "culture",
    "environment",
    "other",
]


def _make_cluster_input(
    index: int = 0,
    article_count: int = 3,
    top_url: str = "http://example.com",
) -> ClusterInput:
    return ClusterInput(
        cluster_index=index,
        titles=[f"Titre {i}" for i in range(article_count)],
        summaries=[f"Résumé {i}" for i in range(article_count)],
        texts=[f"Texte complet {i}" for i in range(article_count)],
        article_count=article_count,
        top_url=top_url,
        publish_date="",
        authors=[],
        category="",
    )


def _make_labeled_cluster(
    index: int = 0,
    article_count: int = 3,
    top_url: str = "http://example.com",
) -> LabeledCluster:
    return LabeledCluster(
        cluster_title=f"Cluster titre {index}",
        cluster_summary=f"Résumé synthétique {index}",
        category="politics",
        article_count=article_count,
        top_url=top_url,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_label_clusters_returns_list_of_labeled_clusters():
    """label_clusters retourne une liste de LabeledCluster avec les mocks."""
    inputs = [_make_cluster_input(i) for i in range(3)]
    expected_clusters = [_make_labeled_cluster(i) for i in range(3)]
    mocked_response = LabeledClusters(clusters=expected_clusters)

    with patch(
        "core.news.labeler.call_llm_structured",
        new=AsyncMock(return_value=mocked_response),
    ):
        result = await label_clusters(inputs)

    assert isinstance(result, list)
    assert all(isinstance(r, LabeledCluster) for r in result)


@pytest.mark.asyncio
async def test_label_clusters_length_matches_inputs():
    """Le nombre de LabeledCluster retournés correspond au nombre d'inputs."""
    n = 5
    inputs = [_make_cluster_input(i) for i in range(n)]
    expected_clusters = [_make_labeled_cluster(i) for i in range(n)]
    mocked_response = LabeledClusters(clusters=expected_clusters)

    with patch(
        "core.news.labeler.call_llm_structured",
        new=AsyncMock(return_value=mocked_response),
    ):
        result = await label_clusters(inputs)

    assert len(result) == n


@pytest.mark.asyncio
async def test_label_clusters_category_is_valid():
    """Chaque LabeledCluster a une catégorie dans la liste des catégories valides."""
    inputs = [_make_cluster_input(0)]
    mocked_response = LabeledClusters(clusters=[_make_labeled_cluster(0)])

    with patch(
        "core.news.labeler.call_llm_structured",
        new=AsyncMock(return_value=mocked_response),
    ):
        result = await label_clusters(inputs)

    for r in result:
        assert r.category in VALID_CATEGORY_VALUES


@pytest.mark.asyncio
async def test_label_clusters_propagates_article_count_and_top_url():
    """article_count et top_url sont bien propagés depuis les LabeledCluster."""
    inputs = [_make_cluster_input(0, article_count=7, top_url="http://specific.com")]
    expected = LabeledCluster(
        cluster_title="Title",
        cluster_summary="Summary",
        category="technology",
        article_count=7,
        top_url="http://specific.com",
    )
    mocked_response = LabeledClusters(clusters=[expected])

    with patch(
        "core.news.labeler.call_llm_structured",
        new=AsyncMock(return_value=mocked_response),
    ):
        result = await label_clusters(inputs)

    assert result[0].article_count == 7
    assert result[0].top_url == "http://specific.com"


@pytest.mark.asyncio
async def test_label_clusters_empty_inputs_returns_empty_without_llm_call():
    """Si inputs est vide, retourne [] sans appeler le LLM."""
    mock_llm = AsyncMock()

    with patch("core.news.labeler.call_llm_structured", new=mock_llm):
        result = await label_clusters([])

    assert result == []
    mock_llm.assert_not_called()


@pytest.mark.asyncio
async def test_label_clusters_calls_llm_with_asyncmock():
    """Vérifie que call_llm_structured est bien appelé une fois avec AsyncMock."""
    inputs = [_make_cluster_input(0), _make_cluster_input(1)]
    mocked_response = LabeledClusters(
        clusters=[_make_labeled_cluster(i) for i in range(2)]
    )
    mock_llm = AsyncMock(return_value=mocked_response)

    with patch("core.news.labeler.call_llm_structured", new=mock_llm):
        await label_clusters(inputs)

    mock_llm.assert_called_once()
