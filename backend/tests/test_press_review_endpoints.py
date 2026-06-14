"""Tests for press review generation endpoints (chat-based)."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from core.security import hash_password
from core.auth import create_access_token
import core.auth as auth
import main
from database.models import User, Chat, Message, MessageType


@pytest.fixture
def client_with_chat() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        pw = hash_password("testpass")
        user = User(email="test@test.com", hashed_password=pw)
        other_user = User(
            email="other@test.com", hashed_password=hash_password("otherpass")
        )
        session.add(user)
        session.add(other_user)
        session.commit()
        session.refresh(user)
        session.refresh(other_user)

        now = datetime.now(timezone.utc).isoformat()
        chat = Chat(user_id=user.id, date=now)
        session.add(chat)
        session.commit()
        session.refresh(chat)

        m1 = Message(
            chat_id=chat.id,
            content="Quels sont les derniers articles sur l'IA?",
            timestamp=now,
            type=MessageType.USER,
        )
        m2 = Message(
            chat_id=chat.id,
            content="Voici un article sur les avancées de l'IA en France.",
            timestamp=now,
            type=MessageType.AI,
        )
        session.add(m1)
        session.add(m2)
        session.commit()

    def override_get_db():
        with Session(engine) as session:
            yield session

    import database.database as _db_mod
    import database.crud as _crud_mod

    _db_mod.engine = engine
    _crud_mod.engine = engine

    app = main.app
    app.dependency_overrides[auth.db.get_db] = override_get_db

    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def noop_lifespan(_app):
        yield

    app.router.lifespan_context = noop_lifespan

    with TestClient(app) as test_client:
        yield test_client

    app.router.lifespan_context = original_lifespan
    app.dependency_overrides.clear()


class TestGenerateChatReview:
    def test_generate_review_requires_auth(self, client_with_chat):
        r = client_with_chat.post("/api/v1/chats/1/review")
        assert r.status_code in (401, 403)

    def test_generate_review_returns_404_for_other_user(self, client_with_chat):
        other_token = create_access_token({"sub": "other@test.com"})
        headers = {"Authorization": f"Bearer {other_token}"}
        r = client_with_chat.post("/api/v1/chats/1/review", headers=headers)
        assert r.status_code == 404

    def test_generate_review_returns_404_for_nonexistent_chat(self, client_with_chat):
        token = create_access_token({"sub": "test@test.com"})
        headers = {"Authorization": f"Bearer {token}"}
        r = client_with_chat.post("/api/v1/chats/999/review", headers=headers)
        assert r.status_code == 404

    def test_generate_review_returns_504_on_llm_timeout(self, client_with_chat):
        token = create_access_token({"sub": "test@test.com"})
        headers = {"Authorization": f"Bearer {token}"}

        with patch("agents.Runner.run", side_effect=TimeoutError()):
            r = client_with_chat.post("/api/v1/chats/1/review", headers=headers)
            assert r.status_code == 504

    def test_generate_review_returns_502_on_llm_error(self, client_with_chat):
        token = create_access_token({"sub": "test@test.com"})
        headers = {"Authorization": f"Bearer {token}"}

        with patch("agents.Runner.run", side_effect=Exception("LLM error")):
            r = client_with_chat.post("/api/v1/chats/1/review", headers=headers)
            assert r.status_code == 502


class TestGetChatReviews:
    def test_get_chat_reviews_requires_auth(self, client_with_chat):
        r = client_with_chat.get("/api/v1/reviews/chats")
        assert r.status_code in (401, 403)

    def test_get_chat_reviews_returns_empty_list(self, client_with_chat):
        token = create_access_token({"sub": "test@test.com"})
        headers = {"Authorization": f"Bearer {token}"}
        r = client_with_chat.get("/api/v1/reviews/chats", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["data"] == []
