"""Tests for bootstrap functions."""

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_bootstrap_demo_user_creates_user_with_limits(db_session):
    """Le compte demo est créé avec expires_at et les quotas."""
    from bootstrap import bootstrap_demo_user
    from database.models import User, UserRole
    from sqlmodel import select
    from datetime import datetime

    result = bootstrap_demo_user(
        email="demo@test.com",
        password="password123",
        expires_days=30,
        worldnews_limit=100,
        llm_tokens_limit=10_000_000,
        db=db_session,
    )
    assert result is True

    user = db_session.exec(select(User).where(User.email == "demo@test.com")).first()
    assert user is not None
    assert user.role == UserRole.USER
    assert user.expires_at is not None
    assert user.expires_at > datetime.now()
    assert user.worldnews_calls_limit == 100
    assert user.llm_tokens_limit == 10_000_000
    assert user.worldnews_calls_used == 0
    assert user.llm_tokens_in_used == 0
    assert user.llm_tokens_out_used == 0


def test_bootstrap_demo_user_is_idempotent(db_session):
    """Appeler bootstrap_demo_user deux fois ne crée pas de doublon."""
    from bootstrap import bootstrap_demo_user

    bootstrap_demo_user("demo@test.com", "pass", 30, 100, 10_000_000, db_session)
    result = bootstrap_demo_user(
        "demo@test.com", "pass", 30, 100, 10_000_000, db_session
    )
    assert result is False
