"""Tests for the press review agent — schema validation, no LLM call."""

import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from pydantic import ValidationError
import pytest


class TestPressReviewOutputSchema:
    def test_valid_output(self):
        from core.agent.press_review_agent import PressReviewOutput, ArticleSummary

        output = PressReviewOutput(
            title="Revue de presse du 14 juin",
            editorial="Synthèse générale des discussions.",
            articles=[
                ArticleSummary(
                    title="Article 1",
                    content="Analyse approfondie de l'article 1 sur trois paragraphes.",
                    source="https://example.com/article1",
                ),
                ArticleSummary(
                    title="Article 2",
                    content="Analyse approfondie de l'article 2 sur trois paragraphes.",
                    source=None,
                ),
            ],
        )
        assert output.title == "Revue de presse du 14 juin"
        assert len(output.articles) == 2
        assert output.articles[0].source == "https://example.com/article1"
        assert output.articles[1].source is None

    def test_empty_articles_list(self):
        from core.agent.press_review_agent import PressReviewOutput

        output = PressReviewOutput(
            title="Test",
            editorial="Synthèse vide.",
            articles=[],
        )
        assert output.articles == []

    def test_serialize_to_json(self):
        from core.agent.press_review_agent import PressReviewOutput, ArticleSummary

        output = PressReviewOutput(
            title="Test",
            editorial="Synthèse éditoriale.",
            articles=[
                ArticleSummary(title="A1", content="Contenu détaillé de l'article."),
            ],
        )
        json_str = output.model_dump_json()
        assert '"title"' in json_str
        assert '"editorial"' in json_str
        assert '"articles"' in json_str
        assert '"A1"' in json_str

    def test_title_required(self):
        from core.agent.press_review_agent import PressReviewOutput

        with pytest.raises(ValidationError):
            PressReviewOutput(editorial="Test", articles=[])
