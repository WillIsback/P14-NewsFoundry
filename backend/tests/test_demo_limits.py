from datetime import datetime, timedelta
import pytest
from fastapi import HTTPException
from database.models import User, UserRole


def make_user(**kwargs):
    defaults = dict(
        id=1,
        email="demo@test.com",
        hashed_password="x",
        role=UserRole.USER,
        expires_at=None,
        worldnews_calls_used=0,
        worldnews_calls_limit=None,
        llm_tokens_in_used=0,
        llm_tokens_out_used=0,
        llm_tokens_limit=None,
    )
    defaults.update(kwargs)
    return User(**defaults)


def test_check_account_expiry_no_limit():
    from api.dependencies.demo_limits import check_account_expiry

    check_account_expiry(make_user())


def test_check_account_expiry_not_expired():
    from api.dependencies.demo_limits import check_account_expiry

    check_account_expiry(make_user(expires_at=datetime.now() + timedelta(days=10)))


def test_check_account_expiry_expired():
    from api.dependencies.demo_limits import check_account_expiry

    with pytest.raises(HTTPException) as exc_info:
        check_account_expiry(make_user(expires_at=datetime.now() - timedelta(days=1)))
    assert exc_info.value.status_code == 403
    assert "expiré" in exc_info.value.detail


def test_check_worldnews_quota_no_limit():
    from api.dependencies.demo_limits import check_worldnews_quota

    check_worldnews_quota(make_user())


def test_check_worldnews_quota_within_limit():
    from api.dependencies.demo_limits import check_worldnews_quota

    check_worldnews_quota(make_user(worldnews_calls_used=5, worldnews_calls_limit=10))


def test_check_worldnews_quota_exceeded():
    from api.dependencies.demo_limits import check_worldnews_quota

    with pytest.raises(HTTPException) as exc_info:
        check_worldnews_quota(
            make_user(worldnews_calls_used=10, worldnews_calls_limit=10)
        )
    assert exc_info.value.status_code == 403
    assert "WorldNewsAPI" in exc_info.value.detail


def test_check_llm_quota_no_limit():
    from api.dependencies.demo_limits import check_llm_quota

    check_llm_quota(make_user())


def test_check_llm_quota_within_limit():
    from api.dependencies.demo_limits import check_llm_quota

    check_llm_quota(
        make_user(
            llm_tokens_in_used=4_000_000,
            llm_tokens_out_used=1_000_000,
            llm_tokens_limit=10_000_000,
        )
    )


def test_check_llm_quota_exceeded():
    from api.dependencies.demo_limits import check_llm_quota

    with pytest.raises(HTTPException) as exc_info:
        check_llm_quota(
            make_user(
                llm_tokens_in_used=8_000_000,
                llm_tokens_out_used=2_000_001,
                llm_tokens_limit=10_000_000,
            )
        )
    assert exc_info.value.status_code == 403
    assert "token" in exc_info.value.detail.lower()
