"""Tests TDD pour core.news.service.fetch_and_build_context.

Phase RED : ces tests doivent échouer avant que le code soit écrit.
"""

from pathlib import Path
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from core.news.labeler import LabeledCluster
from core.news.service import fetch_and_build_context
from core.security import hash_password
from database.models import Chat, TopNewsContext, User
from worldnewsapi.models.top_news200_response import TopNews200Response
from worldnewsapi.models.top_news200_response_top_news_inner import (
    TopNews200ResponseTopNewsInner,
)
from worldnewsapi.models.top_news200_response_top_news_inner_news_inner import (
    TopNews200ResponseTopNewsInnerNewsInner,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mem_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_setup(mem_engine):
    """Session avec user + chat pré-insérés. Yields (session, user, chat)."""
    with Session(mem_engine) as session:
        user = User(email="svc@test.com", hashed_password=hash_password("pw"))
        session.add(user)
        session.commit()
        session.refresh(user)
        chat = Chat(user_id=user.id, date="2026-06-01")
        session.add(chat)
        session.commit()
        session.refresh(chat)
        yield session, user, chat


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_labeled_clusters(n: int = 3) -> list[LabeledCluster]:
    return [
        LabeledCluster(
            cluster_title=f"Cluster {i}",
            cluster_summary=f"Résumé {i}",
            category="politics",  # type: ignore[arg-type]
            article_count=5,
            top_url=f"http://example.com/{i}",
        )
        for i in range(n)
    ]


def _make_top_news_response() -> TopNews200Response:
    article = TopNews200ResponseTopNewsInnerNewsInner(
        id=1,
        title="Titre",
        url="http://example.com/1",
        summary="Résumé",
        publish_date="2026-06-01 10:00:00",
        authors=[],
        text="",
        image=None,
        author=None,
    )
    cluster = TopNews200ResponseTopNewsInner(news=[article])
    return TopNews200Response(top_news=[cluster], language="fr", country="fr")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_and_build_context_creates_topnewscontext(db_setup):
    """fetch_and_build_context crée un TopNewsContext en BDD."""
    session, _, chat = db_setup
    labeled = _make_labeled_clusters(3)
    mock_api = MagicMock()
    mock_api.top_news.return_value = _make_top_news_response()

    with (
        patch("core.news.service.get_news_api", return_value=mock_api),
        patch("core.news.service.label_clusters", new=AsyncMock(return_value=labeled)),
    ):
        ctx = await fetch_and_build_context(
            chat_id=chat.id,
            source_country="fr",
            language="fr",
            date="2026-06-01",
            session=session,
        )

    assert ctx is not None
    assert isinstance(ctx, TopNewsContext)
    assert ctx.id is not None
    assert ctx.chat_id == chat.id


@pytest.mark.asyncio
async def test_fetch_and_build_context_returns_existing_without_api_call(db_setup):
    """Si un contexte existe déjà pour le chat_id, il est retourné sans appel API."""
    session, _, chat = db_setup

    # Pré-créer un contexte
    from database.crud import create_top_news_context

    existing = create_top_news_context(
        session=session,
        chat_id=chat.id,
        date="2026-06-01",
        source_country="fr",
        language="fr",
        system_prompt="existing prompt",
        news=[],
    )

    mock_api = MagicMock()

    with (
        patch("core.news.service.get_news_api", return_value=mock_api),
        patch("core.news.service.label_clusters", new=AsyncMock()) as mock_label,
    ):
        result = await fetch_and_build_context(
            chat_id=chat.id,
            source_country="fr",
            language="fr",
            date="2026-06-01",
            session=session,
        )

    assert result.id == existing.id
    mock_api.top_news.assert_not_called()
    mock_label.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_and_build_context_system_prompt_contains_date(db_setup):
    """Le system_prompt persisté contient la date effective."""
    session, _, chat = db_setup
    labeled = _make_labeled_clusters(2)
    mock_api = MagicMock()
    mock_api.top_news.return_value = _make_top_news_response()

    with (
        patch("core.news.service.get_news_api", return_value=mock_api),
        patch("core.news.service.label_clusters", new=AsyncMock(return_value=labeled)),
    ):
        ctx = await fetch_and_build_context(
            chat_id=chat.id,
            source_country="fr",
            language="fr",
            date="2026-06-01",
            session=session,
        )

    assert "2026-06-01" in ctx.system_prompt


@pytest.mark.asyncio
async def test_fetch_and_build_context_news_contains_expected_keys(db_setup):
    """Le champ news contient des dicts avec les clés title, url, summary, category, article_count."""
    session, _, chat = db_setup
    labeled = _make_labeled_clusters(2)
    mock_api = MagicMock()
    mock_api.top_news.return_value = _make_top_news_response()

    with (
        patch("core.news.service.get_news_api", return_value=mock_api),
        patch("core.news.service.label_clusters", new=AsyncMock(return_value=labeled)),
    ):
        ctx = await fetch_and_build_context(
            chat_id=chat.id,
            source_country="fr",
            language="fr",
            date="2026-06-01",
            session=session,
        )

    assert isinstance(ctx.news, list)
    assert len(ctx.news) == 2
    expected_keys = {"title", "url", "summary", "category", "article_count"}
    for item in ctx.news:
        assert expected_keys.issubset(item.keys())


@pytest.mark.asyncio
async def test_fetch_and_build_context_uses_today_when_date_is_none(db_setup):
    """Sans date fournie, le contexte est créé avec la date du jour."""
    session, _, chat = db_setup
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    labeled = _make_labeled_clusters(1)
    mock_api = MagicMock()
    mock_api.top_news.return_value = _make_top_news_response()

    with (
        patch("core.news.service.get_news_api", return_value=mock_api),
        patch("core.news.service.label_clusters", new=AsyncMock(return_value=labeled)),
    ):
        ctx = await fetch_and_build_context(
            chat_id=chat.id,
            source_country="fr",
            language="fr",
            date=None,
            session=session,
        )

    assert ctx.date == today
