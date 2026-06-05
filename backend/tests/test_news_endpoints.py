"""Tests TDD pour les endpoints news (POST /news/context, GET /news/context/{chat_id}).

Phase RED : ces tests doivent échouer avant que le code soit écrit.
"""

from pathlib import Path
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from sqlmodel import Session

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from core.auth import create_access_token
from core.security import hash_password
from database.models import Chat, TopNewsContext, User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_headers(email: str) -> dict[str, str]:
    token = create_access_token({"sub": email})
    return {"Authorization": f"Bearer {token}"}


def _make_fake_context(chat_id: int) -> TopNewsContext:
    now = datetime.now(timezone.utc).isoformat()
    return TopNewsContext(
        id=1,
        chat_id=chat_id,
        date="2026-06-01",
        source_country="fr",
        language="fr",
        system_prompt="Tu es NewsFoundry. Voici les actualités...",
        news=[
            {
                "title": "Actualité 1",
                "url": "http://example.com/1",
                "summary": "Résumé 1",
                "category": "politics",
                "article_count": 5,
            }
        ],
        created_at=now,
    )


# ---------------------------------------------------------------------------
# Tests POST /api/v1/news/context
# ---------------------------------------------------------------------------


def test_create_news_context_without_auth_returns_401(client):
    """POST /api/v1/news/context sans token → 401."""
    response = client.post(
        "/api/v1/news/context",
        json={"chat_id": 1, "source_country": "fr", "language": "fr"},
    )
    assert response.status_code == 401


def test_create_news_context_with_auth_returns_201(client, engine):
    """POST /api/v1/news/context avec auth et mock service → 201 avec NewsContextPublic."""
    # Créer user + chat en DB
    with Session(engine) as session:
        user = User(email="news@test.com", hashed_password=hash_password("pw"))
        session.add(user)
        session.commit()
        session.refresh(user)
        chat = Chat(user_id=user.id, date="2026-06-01")
        session.add(chat)
        session.commit()
        session.refresh(chat)
        chat_id = chat.id

    headers = _auth_headers("news@test.com")
    fake_ctx = _make_fake_context(chat_id)

    with patch(
        "api.news_endpoints.fetch_and_build_context",
        new=AsyncMock(return_value=fake_ctx),
    ):
        response = client.post(
            "/api/v1/news/context",
            json={"chat_id": chat_id, "source_country": "fr", "language": "fr"},
            headers=headers,
        )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["chat_id"] == chat_id
    assert data["source_country"] == "fr"
    assert data["language"] == "fr"
    assert isinstance(data["news"], list)


def test_create_news_context_response_has_newscontextpublic_fields(client, engine):
    """La réponse contient bien tous les champs de NewsContextPublic."""
    with Session(engine) as session:
        user = User(email="news2@test.com", hashed_password=hash_password("pw"))
        session.add(user)
        session.commit()
        session.refresh(user)
        chat = Chat(user_id=user.id, date="2026-06-01")
        session.add(chat)
        session.commit()
        session.refresh(chat)
        chat_id = chat.id

    headers = _auth_headers("news2@test.com")
    fake_ctx = _make_fake_context(chat_id)

    with patch(
        "api.news_endpoints.fetch_and_build_context",
        new=AsyncMock(return_value=fake_ctx),
    ):
        response = client.post(
            "/api/v1/news/context",
            json={"chat_id": chat_id},
            headers=headers,
        )

    data = response.json()["data"]
    required_fields = {
        "id",
        "chat_id",
        "date",
        "source_country",
        "language",
        "system_prompt",
        "news",
        "created_at",
    }
    assert required_fields.issubset(data.keys())


# ---------------------------------------------------------------------------
# Tests GET /api/v1/news/context/{chat_id}
# ---------------------------------------------------------------------------


def test_get_news_context_without_auth_returns_401(client):
    """GET /api/v1/news/context/{chat_id} sans token → 401."""
    response = client.get("/api/v1/news/context/1")
    assert response.status_code == 401


def test_get_news_context_returns_200_when_exists(client, engine):
    """GET /api/v1/news/context/{chat_id} avec contexte existant → 200."""
    with Session(engine) as session:
        user = User(email="news3@test.com", hashed_password=hash_password("pw"))
        session.add(user)
        session.commit()
        session.refresh(user)
        chat = Chat(user_id=user.id, date="2026-06-01")
        session.add(chat)
        session.commit()
        session.refresh(chat)
        chat_id = chat.id

        now = datetime.now(timezone.utc).isoformat()
        ctx = TopNewsContext(
            chat_id=chat_id,
            date="2026-06-01",
            source_country="fr",
            language="fr",
            system_prompt="prompt",
            news=[{"title": "Test"}],
            created_at=now,
        )
        session.add(ctx)
        session.commit()
        session.refresh(ctx)

    headers = _auth_headers("news3@test.com")
    response = client.get(f"/api/v1/news/context/{chat_id}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["chat_id"] == chat_id


def test_get_news_context_returns_404_when_absent(client, engine):
    """GET /api/v1/news/context/{chat_id} avec chat sans contexte → 404."""
    with Session(engine) as session:
        user = User(email="news4@test.com", hashed_password=hash_password("pw"))
        session.add(user)
        session.commit()
        session.refresh(user)

    headers = _auth_headers("news4@test.com")
    response = client.get("/api/v1/news/context/99999", headers=headers)

    assert response.status_code == 404
