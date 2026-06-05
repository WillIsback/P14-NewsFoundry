"""Tests TDD pour core.prompts.build_news_system_prompt.

Phase RED : ces tests doivent échouer avant que le code soit écrit.
"""

from pathlib import Path
import sys


BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from core.news.labeler import LabeledCluster
from core.prompts import CLUSTER_LABELING_PROMPT, build_news_system_prompt


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_labeled_cluster(
    index: int = 0,
    category: str = "politics",
    article_count: int = 3,
) -> LabeledCluster:
    return LabeledCluster(
        cluster_title=f"Titre cluster {index}",
        cluster_summary=f"Résumé du cluster {index}",
        category=category,  # type: ignore[arg-type]
        article_count=article_count,
        top_url=f"http://example.com/{index}",
    )


# ---------------------------------------------------------------------------
# Tests build_news_system_prompt
# ---------------------------------------------------------------------------


def test_build_news_system_prompt_returns_non_empty_string():
    """Avec 3 clusters, retourne une string non vide."""
    clusters = [_make_labeled_cluster(i) for i in range(3)]
    result = build_news_system_prompt("2026-06-01", clusters)
    assert isinstance(result, str)
    assert len(result) > 0


def test_build_news_system_prompt_contains_date():
    """La string résultante contient la date."""
    clusters = [_make_labeled_cluster(0)]
    result = build_news_system_prompt("2026-06-01", clusters)
    assert "2026-06-01" in result


def test_build_news_system_prompt_contains_category_in_brackets():
    """Chaque catégorie apparaît entre crochets dans le résultat."""
    clusters = [
        _make_labeled_cluster(0, category="politics"),
        _make_labeled_cluster(1, category="technology"),
        _make_labeled_cluster(2, category="sports"),
    ]
    result = build_news_system_prompt("2026-06-01", clusters)
    assert "[politics]" in result
    assert "[technology]" in result
    assert "[sports]" in result


def test_build_news_system_prompt_cluster_count_in_header():
    """Le nombre de clusters est mentionné dans l'en-tête."""
    n = 5
    clusters = [_make_labeled_cluster(i) for i in range(n)]
    result = build_news_system_prompt("2026-06-01", clusters)
    assert str(n) in result


def test_build_news_system_prompt_empty_list_does_not_crash():
    """Avec une liste vide, retourne une string valide (sans crash)."""
    result = build_news_system_prompt("2026-06-01", [])
    assert isinstance(result, str)
    assert "2026-06-01" in result


def test_build_news_system_prompt_contains_cluster_titles():
    """Les titres des clusters apparaissent dans le résultat."""
    cluster = _make_labeled_cluster(0)
    result = build_news_system_prompt("2026-06-01", [cluster])
    assert cluster.cluster_title in result


def test_build_news_system_prompt_contains_top_url():
    """Les URLs des clusters apparaissent dans le résultat."""
    cluster = _make_labeled_cluster(0)
    result = build_news_system_prompt("2026-06-01", [cluster])
    assert cluster.top_url in result


# ---------------------------------------------------------------------------
# Tests CLUSTER_LABELING_PROMPT
# ---------------------------------------------------------------------------


def test_cluster_labeling_prompt_is_non_empty_string():
    """CLUSTER_LABELING_PROMPT est une string non vide."""
    assert isinstance(CLUSTER_LABELING_PROMPT, str)
    assert len(CLUSTER_LABELING_PROMPT) > 0


def test_cluster_labeling_prompt_mentions_categories():
    """CLUSTER_LABELING_PROMPT mentionne les catégories attendues."""
    assert "politics" in CLUSTER_LABELING_PROMPT
    assert "technology" in CLUSTER_LABELING_PROMPT
