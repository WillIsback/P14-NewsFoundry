from datetime import datetime, timezone
from fastapi import HTTPException
from sqlmodel import Session

from database.models import User


def check_account_expiry(current_user: User) -> None:
    """Lève HTTP 403 si le compte demo est expiré."""
    if current_user.expires_at is None:
        return
    # Comparaison naive vs naive pour cohérence avec le stockage DB
    expires = current_user.expires_at
    now = (
        datetime.now(tz=timezone.utc).replace(tzinfo=None)
        if expires.tzinfo is None
        else datetime.now(tz=timezone.utc)
    )
    if now > expires:
        raise HTTPException(
            status_code=403,
            detail="Compte demo expiré. Contactez l'administrateur.",
        )


def check_worldnews_quota(current_user: User) -> None:
    """Lève HTTP 403 si le quota WorldNewsAPI est atteint."""
    if current_user.worldnews_calls_limit is None:
        return
    if current_user.worldnews_calls_used >= current_user.worldnews_calls_limit:
        raise HTTPException(
            status_code=403,
            detail="Quota WorldNewsAPI du compte demo atteint. Contactez l'administrateur.",
        )


def check_llm_quota(current_user: User) -> None:
    """Lève HTTP 403 si le quota de tokens LLM est atteint."""
    if current_user.llm_tokens_limit is None:
        return
    total_used = current_user.llm_tokens_in_used + current_user.llm_tokens_out_used
    if total_used >= current_user.llm_tokens_limit:
        raise HTTPException(
            status_code=403,
            detail="Limite de tokens LLM du compte demo atteinte (10M). Contactez l'administrateur.",
        )


def track_llm_tokens(
    current_user: User, tokens_in: int, tokens_out: int, db: Session
) -> None:
    """Incrémente les compteurs de tokens LLM pour les comptes demo."""
    if current_user.llm_tokens_limit is None:
        return
    current_user.llm_tokens_in_used += tokens_in
    current_user.llm_tokens_out_used += tokens_out
    db.add(current_user)
    db.commit()


def increment_worldnews_calls(current_user: User, db: Session) -> None:
    """Incrémente le compteur d'appels WorldNewsAPI pour les comptes demo."""
    if current_user.worldnews_calls_limit is None:
        return
    current_user.worldnews_calls_used += 1
    db.add(current_user)
    db.commit()
