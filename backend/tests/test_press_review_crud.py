import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from database import crud
from database.models import Chat


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    # Patch the global engine so sync wrappers use our in-memory one
    crud.engine = engine
    return engine


@pytest.fixture
def chat(engine):
    with Session(engine) as session:
        c = Chat(user_id=1, date=datetime.now(timezone.utc).isoformat())
        session.add(c)
        session.commit()
        session.refresh(c)
        return c


def test_update_chat_press_review(engine, chat):
    review_title = "Revue de presse test"
    review_summary = "Synthèse générale de test"
    review_articles = '[{"title": "Article 1", "summary": "Résumé article 1"}]'
    review_date = "2026-06-14T12:00:00"

    crud.update_chat_press_review_sync(
        chat.id, review_title, review_summary, review_articles, review_date
    )

    with Session(engine) as session:
        updated = session.get(Chat, chat.id)
        assert updated is not None
        assert updated.press_review_title == review_title
        assert updated.press_review_summary == review_summary
        assert updated.press_review_articles == review_articles
        assert updated.press_review_date == review_date


def test_update_chat_press_review_nonexistent_chat(engine):
    crud.update_chat_press_review_sync(999, "Title", "Summary", "[]", "2026-06-14")
