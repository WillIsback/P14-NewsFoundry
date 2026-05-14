from pathlib import Path
import sys
from collections.abc import Generator

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from contextlib import asynccontextmanager

# Ensure backend/src is importable when tests run from backend/.
BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

import core.auth as auth
import main
from core.config import API_LOGIN_RATE_LIMIT_REQUESTS
from database.database import Database
from database.models import User


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        hashed_password = bcrypt.hashpw(
            "test".encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        session.add(User(email="test@test.com", hashed_password=hashed_password))
        session.commit()

    def override_get_db():
        with Session(engine) as session:
            yield session

    app = main.app

    # Override auth dependency used by verify_user.
    app.dependency_overrides[auth.db.get_db] = override_get_db

    # Override router-level db dependency captured during app factory setup.
    for route in app.routes:
        dependant = getattr(route, "dependant", None)
        if dependant is None:
            continue
        for dep in dependant.dependencies:
            call = dep.call
            if callable(call) and getattr(call, "__name__", "") == "get_db":
                owner = getattr(call, "__self__", None)
                if isinstance(owner, Database):
                    app.dependency_overrides[call] = override_get_db

    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def noop_lifespan(_app):
        yield

    app.router.lifespan_context = noop_lifespan

    with TestClient(app) as test_client:
        yield test_client

    app.router.lifespan_context = original_lifespan
    app.dependency_overrides.clear()


def test_login_with_valid_credentials_returns_token_and_email(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@test.com", "password": "test"},  # NOSONAR
        headers={"x-forwarded-for": "10.0.0.1"},  # NOSONAR
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["status"] == 200
    assert payload["error"] is None
    assert payload["data"]["token_type"] == "bearer"
    assert isinstance(payload["data"]["access_token"], str)
    assert payload["data"]["access_token"]
    assert payload["data"]["email"] == "test@test.com"


def test_login_with_invalid_credentials_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@test.com", "password": "wrong_password"},  # NOSONAR
        headers={"x-forwarded-for": "10.0.0.2"},  # NOSONAR
    )

    assert response.status_code == 401
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"] is not None


def test_login_with_malformed_json_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@test.com"},  # missing password
        headers={"x-forwarded-for": "10.0.0.3"},  # NOSONAR
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "VALIDATION_ERROR"


def test_login_with_invalid_email_format_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "invalid-email", "password": "test"},  # NOSONAR
        headers={"x-forwarded-for": "10.0.0.7"},  # NOSONAR
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    assert any(err["loc"][-1] == "email" for err in payload["error"]["details"])


def test_login_with_nonexistent_user_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@test.com", "password": "test"},  # NOSONAR
        headers={"x-forwarded-for": "10.0.0.4"},  # NOSONAR
    )

    assert response.status_code == 401
    payload = response.json()
    assert payload["success"] is False


def test_protected_rejects_missing_or_invalid_token(client: TestClient) -> None:
    missing_token_response = client.get("/api/v1/auth/protected")
    assert missing_token_response.status_code == 401
    missing_payload = missing_token_response.json()
    assert missing_payload["success"] is False
    assert missing_payload["error"]["code"] == "HTTP_EXCEPTION"

    invalid_token_response = client.get(
        "/api/v1/auth/protected",
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert invalid_token_response.status_code == 401
    invalid_payload = invalid_token_response.json()
    assert invalid_payload["success"] is False
    assert invalid_payload["error"]["code"] == "HTTP_EXCEPTION"


def test_protected_allows_valid_token_only(client: TestClient) -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@test.com", "password": "test"},  # NOSONAR
        headers={"x-forwarded-for": "10.0.0.5"},  # NOSONAR
    )
    token = login_response.json()["data"]["access_token"]

    protected_response = client.get(
        "/api/v1/auth/protected",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert protected_response.status_code == 200
    payload = protected_response.json()
    assert payload["success"] is True
    message = payload["data"]["message"]
    assert "test@test.com" in message


def test_token_validation_extracts_correct_user_email(client: TestClient) -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@test.com", "password": "test"},  # NOSONAR
        headers={"x-forwarded-for": "10.0.0.6"},  # NOSONAR
    )
    assert login_response.status_code == 200
    data = login_response.json()["data"]
    assert data["email"] == "test@test.com"

    token = data["access_token"]
    protected_response = client.get(
        "/api/v1/auth/protected",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert protected_response.status_code == 200
    protected_data = protected_response.json()["data"]
    assert "test@test.com" in protected_data["message"]


def test_swagger_ui_is_on_api_docs(client: TestClient) -> None:
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()


def test_old_docs_route_is_gone(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 404


def test_openapi_json_always_accessible(client: TestClient) -> None:
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    payload = response.json()
    assert "openapi" in payload
    assert payload["info"]["title"] == "NewsFoundry backend API"


def test_login_rate_limit_returns_429_after_limit_for_same_ip(
    client: TestClient,
) -> None:
    ip_headers = {"x-forwarded-for": "10.0.1.250"}  # NOSONAR

    for _ in range(API_LOGIN_RATE_LIMIT_REQUESTS):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "wrong_password"},  # NOSONAR
            headers=ip_headers,
        )
        assert response.status_code == 401
        payload = response.json()
        assert payload["success"] is False

    sixth_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@test.com", "password": "wrong_password"},  # NOSONAR
        headers=ip_headers,
    )

    assert sixth_response.status_code == 429
    payload = sixth_response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert payload["error"]["details"]["retry_after_seconds"] >= 1
    assert "Retry-After" in sixth_response.headers
    assert sixth_response.headers["X-RateLimit-Remaining"] == "0"
    assert sixth_response.headers["X-RateLimit-Limit"] == str(
        API_LOGIN_RATE_LIMIT_REQUESTS
    )
