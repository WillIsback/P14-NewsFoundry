from pathlib import Path
import sys
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone

# Ensure backend/src is importable
BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from core.security import hash_password
import core.auth as auth
import main
from database.models import User, Chat, Message, MessageType


@pytest.fixture
def client_two_users() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # create tables
    SQLModel.metadata.create_all(engine)

    # seed two users + a chat owned by first user with two messages
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

        # two messages (user + ai)
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

    def override_get_db():
        with Session(engine) as session:
            yield session

    app = main.app

    # override auth dependency used by verify_user
    app.dependency_overrides[auth.db.get_db] = override_get_db

    # also patch database engine used by sync crud wrappers so endpoints
    # that call `..._sync` use the same in-memory DB
    import database.database as _db_mod
    import database.crud as _crud_mod

    _db_mod.engine = engine
    _crud_mod.engine = engine

    original_lifespan = app.router.lifespan_context

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def noop_lifespan(_app):
        yield

    app.router.lifespan_context = noop_lifespan

    with TestClient(app) as test_client:
        yield test_client

    app.router.lifespan_context = original_lifespan
    app.dependency_overrides.clear()


def test_owner_can_read_their_chat_messages(client_two_users: TestClient) -> None:
    # build token for owner and request messages
    from core.auth import create_access_token

    token = create_access_token({"sub": "owner@test.com"})
    headers = {"Authorization": f"Bearer {token}"}

    # retrieve chat list to locate chat id
    r = client_two_users.get("/api/v1/chats", headers=headers)
    assert r.status_code == 200
    data = r.json().get("data", [])
    assert len(data) >= 1
    chat_id = data[0]["id"]

    r2 = client_two_users.get(f"/api/v1/chats/{chat_id}/messages", headers=headers)
    assert r2.status_code == 200
    msgs = r2.json().get("data", [])
    assert isinstance(msgs, list)
    assert len(msgs) >= 2


def test_other_user_cannot_access_or_modify_owner_chat(
    client_two_users: TestClient,
) -> None:
    from core.auth import create_access_token

    owner_token = create_access_token({"sub": "owner@test.com"})
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    other_token = create_access_token({"sub": "other@test.com"})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # owner: get chat id
    r = client_two_users.get("/api/v1/chats", headers=owner_headers)
    assert r.status_code == 200
    chat_id = r.json().get("data", [])[0]["id"]

    # other user should get 404 when reading messages
    r_read = client_two_users.get(
        f"/api/v1/chats/{chat_id}/messages", headers=other_headers
    )
    assert r_read.status_code == 404

    # other user should get 404 when trying to post a message
    r_post = client_two_users.post(
        f"/api/v1/chats/{chat_id}/message",
        json={"content": "Intrusion attempt"},
        headers=other_headers,
    )
    assert r_post.status_code == 404
