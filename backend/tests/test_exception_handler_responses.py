"""Tests that exception handlers return correct HTTP status codes.

These tests cover the exact behaviors that fail in the wet E2E test
(issue #159): routes that should return 404, 422 or 200 were returning
502 on Railway production.  They act as regression guards ensuring the
exception-handler plumbing never silently breaks again.
"""

from datetime import datetime, timezone
from pathlib import Path
import sys

from fastapi.testclient import TestClient
from sqlmodel import Session

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from core.auth import create_access_token
from core.security import hash_password
from database.models import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_headers(email: str) -> dict[str, str]:
    token = create_access_token({"sub": email})
    return {"Authorization": f"Bearer {token}"}


def _seed_user(engine, email: str = "user@test.com", password: str = "pass") -> User:
    with Session(engine) as session:
        user = User(email=email, hashed_password=hash_password(password))
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


# ---------------------------------------------------------------------------
# 1. GET /chats/{id}/messages — HTTPException(404) handler
# ---------------------------------------------------------------------------


def test_get_messages_nonexistent_chat_returns_404(client: TestClient, engine) -> None:
    """Route doit retourner 404 pour un chat qui n'existe pas — pas 500 ni 502."""
    _seed_user(engine)
    headers = _auth_headers("user@test.com")

    r = client.get("/api/v1/chats/999999/messages", headers=headers)

    assert r.status_code == 404, (
        f"Attendu 404, reçu {r.status_code}. "
        "Vérifier que le HTTPException handler est bien enregistré."
    )
    body = r.json()
    assert body.get("success") is False


def test_get_messages_other_user_chat_returns_404(client: TestClient, engine) -> None:
    """Route retourne 404 pour un chat appartenant à un autre utilisateur."""
    from database.models import Chat

    _seed_user(engine, "owner@test.com")
    _seed_user(engine, "intruder@test.com", "other")

    with Session(engine) as session:
        chat = Chat(user_id=1, date=datetime.now(timezone.utc).isoformat())
        session.add(chat)
        session.commit()
        session.refresh(chat)
        chat_id = chat.id

    headers = _auth_headers("intruder@test.com")
    r = client.get(f"/api/v1/chats/{chat_id}/messages", headers=headers)

    assert r.status_code == 404


# ---------------------------------------------------------------------------
# 2. POST /chats/message — RequestValidationError(422) handler
# ---------------------------------------------------------------------------


def test_post_chat_message_empty_content_returns_422(
    client: TestClient, engine
) -> None:
    """Contenu vide doit déclencher la validation Pydantic → 422, pas 502."""
    _seed_user(engine)
    headers = _auth_headers("user@test.com")

    r = client.post(
        "/api/v1/chats/message",
        json={"content": ""},
        headers=headers,
    )

    assert r.status_code == 422, (
        f"Attendu 422, reçu {r.status_code}. "
        "Vérifier que le RequestValidationError handler est bien enregistré."
    )
    body = r.json()
    assert body.get("success") is False


def test_post_chat_message_missing_content_returns_422(
    client: TestClient, engine
) -> None:
    """Corps sans champ 'content' doit retourner 422."""
    _seed_user(engine)
    headers = _auth_headers("user@test.com")

    r = client.post("/api/v1/chats/message", json={}, headers=headers)

    assert r.status_code == 422


# ---------------------------------------------------------------------------
# 3. GET /reviews — réponse 200 normale sans exception
# ---------------------------------------------------------------------------


def test_get_reviews_authenticated_returns_200_empty_list(
    client: TestClient, engine
) -> None:
    """GET /reviews avec un token valide doit retourner 200 + liste vide."""
    _seed_user(engine)
    headers = _auth_headers("user@test.com")

    r = client.get("/api/v1/reviews", headers=headers)

    assert r.status_code == 200, (
        f"Attendu 200, reçu {r.status_code}. "
        "Vérifier que la route /reviews répond correctement."
    )
    body = r.json()
    assert body.get("success") is True
    assert isinstance(body.get("data"), list)


def test_get_reviews_unauthenticated_returns_401(client: TestClient) -> None:
    """GET /reviews sans token doit retourner 401."""
    r = client.get("/api/v1/reviews")
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# 4. POST /reviews — RequestValidationError(422) handler
# ---------------------------------------------------------------------------


def test_post_reviews_empty_articles_returns_422(client: TestClient, engine) -> None:
    """POST /reviews avec articles vide doit retourner 422 via Pydantic."""
    _seed_user(engine)
    headers = _auth_headers("user@test.com")

    r = client.post("/api/v1/reviews", json={"articles": ""}, headers=headers)

    assert r.status_code == 422, (
        f"Attendu 422, reçu {r.status_code}. "
        "Vérifier que le RequestValidationError handler est bien enregistré."
    )
