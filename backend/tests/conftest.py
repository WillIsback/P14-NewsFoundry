import os
from pathlib import Path
import sys
from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

# Ensure backend/src is importable
BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

# Make tests deterministic and safe: set test-friendly env vars
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("PYTEST_VERSION", "1")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci")

import core.auth as auth
import main
from database import database as _db_mod
from database import crud as _crud_mod
from core.security import hash_password
from database.models import User, Chat, Message, MessageType
from datetime import datetime, timezone


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def client(engine) -> TestClient:
    # Individual tests or fixtures populate data as needed; engine is already
    # initialised by the engine fixture (SQLModel.metadata.create_all).
    with Session(engine):
        pass

    def override_get_db():
        with Session(engine) as session:
            yield session

    app = main.app

    # override auth DB dependency
    app.dependency_overrides[auth.db.get_db] = override_get_db

    # ensure sync wrappers use our in-memory engine
    _db_mod.engine = engine
    _crud_mod.engine = engine

    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def noop_lifespan(_app):
        yield

    app.router.lifespan_context = noop_lifespan

    with TestClient(app) as test_client:
        yield test_client

    app.router.lifespan_context = original_lifespan
    app.dependency_overrides.clear()


@pytest.fixture
def client_two_users(engine, client):
    # seed two users and a chat owned by first user
    with Session(engine) as session:
        pw1 = hash_password("ownerpass")
        pw2 = hash_password("otherpass")
        owner = User(email="owner@test.com", hashed_password=pw1)
        other = User(email="other@test.com", hashed_password=pw2)
        session.add(owner)
        session.add(other)
        session.commit()
        session.refresh(owner)
        session.refresh(other)

        now = datetime.now(timezone.utc).isoformat()
        chat = Chat(user_id=owner.id, date=now)
        session.add(chat)
        session.commit()
        session.refresh(chat)

        m1 = Message(
            chat_id=chat.id, content="Hi", timestamp=now, type=MessageType.USER
        )
        m2 = Message(
            chat_id=chat.id,
            content="Hello AI reply",
            timestamp=now,
            type=MessageType.AI,
        )
        session.add(m1)
        session.add(m2)
        session.commit()

    return client
