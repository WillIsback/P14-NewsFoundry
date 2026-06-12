"""Tests TDD pour le modèle TopNewsContext et son CRUD.

Phase RED : ces tests doivent échouer avant que le code soit écrit.
"""

from pathlib import Path
import sys

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from core.security import hash_password
from database.crud import create_top_news_context, get_top_news_context_by_chat
from database.models import Chat, TopNewsContext, User


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
        user = User(email="test@example.com", hashed_password=hash_password("pw"))
        session.add(user)
        session.commit()
        session.refresh(user)
        chat = Chat(user_id=user.id, date="2026-06-01")
        session.add(chat)
        session.commit()
        session.refresh(chat)
        yield session, user, chat


# ---------------------------------------------------------------------------
# Tests modèle — structure de la table
# ---------------------------------------------------------------------------


def test_topnewscontext_table_exists(mem_engine):
    """La table 'topnewscontext' doit être créée par SQLModel.metadata.create_all."""
    inspector = inspect(mem_engine)
    assert "topnewscontext" in inspector.get_table_names()


def test_insert_and_retrieve(db_setup):
    """Un TopNewsContext peut être inséré et récupéré avec tous ses champs."""
    session, _, chat = db_setup
    ctx = TopNewsContext(
        chat_id=chat.id,
        date="2026-06-01",
        source_country="fr",
        language="fr",
        system_prompt="test prompt",
        news=[{"title": "News 1", "url": "http://example.com"}],
        created_at="2026-06-01T12:00:00Z",
    )
    session.add(ctx)
    session.commit()
    session.refresh(ctx)

    assert ctx.id is not None
    retrieved = session.get(TopNewsContext, ctx.id)
    assert retrieved is not None
    assert retrieved.chat_id == chat.id
    assert retrieved.date == "2026-06-01"
    assert retrieved.source_country == "fr"
    assert retrieved.language == "fr"


def test_unique_constraint_on_chat_id(db_setup):
    """Insérer deux TopNewsContext avec le même chat_id lève IntegrityError."""
    session, _, chat = db_setup
    ctx1 = TopNewsContext(
        chat_id=chat.id,
        date="2026-06-01",
        source_country="fr",
        language="fr",
        system_prompt="prompt",
        news=[],
        created_at="2026-06-01T12:00:00Z",
    )
    session.add(ctx1)
    session.commit()

    ctx2 = TopNewsContext(
        chat_id=chat.id,
        date="2026-06-01",
        source_country="fr",
        language="fr",
        system_prompt="other prompt",
        news=[],
        created_at="2026-06-01T12:00:01Z",
    )
    session.add(ctx2)
    with pytest.raises(IntegrityError):
        session.commit()


def test_news_field_accepts_list_of_dicts(db_setup):
    """Le champ news accepte list[dict] et restitue la même structure."""
    session, _, chat = db_setup
    news_data = [
        {"title": "Article 1", "url": "http://example.com/1", "category": "politics"},
        {"title": "Article 2", "url": "http://example.com/2", "category": "sports"},
    ]
    ctx = TopNewsContext(
        chat_id=chat.id,
        date="2026-06-01",
        source_country="fr",
        language="fr",
        system_prompt="prompt",
        news=news_data,
        created_at="2026-06-01T12:00:00Z",
    )
    session.add(ctx)
    session.commit()
    session.refresh(ctx)

    assert ctx.news == news_data


# ---------------------------------------------------------------------------
# Tests CRUD
# ---------------------------------------------------------------------------


def test_create_top_news_context_returns_with_id(db_setup):
    """create_top_news_context retourne un objet avec id non-None."""
    session, _, chat = db_setup
    ctx = create_top_news_context(
        session=session,
        chat_id=chat.id,
        date="2026-06-01",
        source_country="fr",
        language="fr",
        system_prompt="System prompt",
        news=[{"title": "t1"}],
    )
    assert ctx.id is not None
    assert ctx.chat_id == chat.id
    assert ctx.created_at is not None


def test_get_top_news_context_by_chat_returns_none_when_absent(db_setup):
    """get_top_news_context_by_chat retourne None si aucun contexte n'existe."""
    session, _, _ = db_setup
    result = get_top_news_context_by_chat(session, chat_id=99999)
    assert result is None


def test_get_top_news_context_by_chat_returns_object(db_setup):
    """get_top_news_context_by_chat retourne l'objet si le contexte existe."""
    session, _, chat = db_setup
    ctx = create_top_news_context(
        session=session,
        chat_id=chat.id,
        date="2026-06-01",
        source_country="fr",
        language="fr",
        system_prompt="System prompt",
        news=[],
    )
    found = get_top_news_context_by_chat(session, chat.id)
    assert found is not None
    assert found.id == ctx.id


def test_news_serialized_deserialized_correctly(db_setup):
    """Le champ news est correctement sérialisé en DB et désérialisé à la lecture."""
    session, _, chat = db_setup
    original_news = [{"title": "A", "url": "http://a.com"}, {"title": "B"}]
    ctx = create_top_news_context(
        session=session,
        chat_id=chat.id,
        date="2026-06-01",
        source_country="fr",
        language="fr",
        system_prompt="prompt",
        news=original_news,
    )
    # Expirer le cache SQLAlchemy pour forcer un vrai rechargement depuis la DB
    session.expire(ctx)
    retrieved = session.get(TopNewsContext, ctx.id)
    assert retrieved is not None
    assert retrieved.news == original_news
