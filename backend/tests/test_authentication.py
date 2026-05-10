from pathlib import Path
import sys

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

# Ensure backend/src is importable when tests run from backend/.
BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

import core.auth as auth
import main
from database.models import User


@pytest.fixture
def client() -> TestClient:
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

    main.app.dependency_overrides[main.db.get_db] = override_get_db
    main.app.dependency_overrides[auth.db.get_db] = override_get_db
    original_init_db = main.db.init_db
    main.db.init_db = lambda: None

    with TestClient(main.app) as test_client:
        yield test_client

    main.db.init_db = original_init_db
    main.app.dependency_overrides.clear()


def test_login_returns_bearer_token(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"email": "test@test.com", "password": "test"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["status"] == 200
    assert payload["error"] is None
    assert payload["data"]["token_type"] == "bearer"
    assert isinstance(payload["data"]["access_token"], str)
    assert payload["data"]["access_token"]


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
        data={"email": "test@test.com", "password": "test"},
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


def test_swagger_ui_is_on_api_docs(client: TestClient) -> None:
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()


def test_old_docs_route_is_gone(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 404


def test_openapi_json_always_accessible(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    payload = response.json()
    assert "openapi" in payload
    assert payload["info"]["title"] == "NewsFoundry backend API"
