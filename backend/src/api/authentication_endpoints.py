from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from api.models import (
    AccessTokenData,
    ApiResponse,
    LoginRequest,
    MessageData,
    UserPublic,
    UserUsage,
    success_response,
)
from core.auth import create_access_token, verify_user
from core.security import hash_password, verify_password
from database.database import Database
from database.models import User

from api.dependencies.demo_limits import check_account_expiry

# Bcrypt hash of a fixed dummy password. Used to keep comparable verification
# cost when the user does not exist, reducing account-enumeration timing leaks.
DUMMY_BCRYPT_HASH = hash_password("timing-check-placeholder")


def get_verified_user(current_user: Annotated[User, Depends(verify_user)]) -> User:
    """Dépendance composée : authentification + vérification expiration demo."""
    check_account_expiry(current_user)
    return current_user


def build_authentication_router(db: Database) -> APIRouter:
    router = APIRouter(tags=["authentication"])

    @router.post("/login")
    def login(
        credentials: LoginRequest,
        session: Annotated[Session, Depends(db.get_db)],
    ) -> ApiResponse[AccessTokenData]:
        user = session.exec(select(User).where(User.email == credentials.email)).first()

        password_hash = user.hashed_password if user else DUMMY_BCRYPT_HASH
        password_is_valid = verify_password(credentials.password, password_hash)

        if not user or not password_is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Identifiant ou mot de passe incorrect",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(data={"sub": user.email})
        return success_response(
            status=status.HTTP_200_OK,
            message="Login successful",
            data=AccessTokenData(
                access_token=access_token, token_type="bearer", email=user.email
            ),
        )

    @router.get("/protected")
    def protected_resource(
        current_user: Annotated[User, Depends(get_verified_user)],
    ) -> ApiResponse[MessageData]:
        return success_response(
            status=status.HTTP_200_OK,
            message="Access granted",
            data=MessageData(
                message=f"Hello, {current_user.email}! This is a protected resource."
            ),
        )

    @router.get("/users/me")
    def me(
        current_user: Annotated[User, Depends(get_verified_user)],
    ) -> ApiResponse[UserPublic]:
        return success_response(
            status=status.HTTP_200_OK,
            message="Current user retrieved",
            data=UserPublic(
                id=current_user.id,  # type: ignore[arg-type]
                email=current_user.email,
                expires_at=current_user.expires_at,
                worldnews_calls_used=current_user.worldnews_calls_used,
                worldnews_calls_limit=current_user.worldnews_calls_limit,
                llm_tokens_in_used=current_user.llm_tokens_in_used,
                llm_tokens_out_used=current_user.llm_tokens_out_used,
                llm_tokens_limit=current_user.llm_tokens_limit,
            ),
        )

    @router.get("/users/me/usage")
    def me_usage(
        current_user: Annotated[User, Depends(verify_user)],
    ) -> ApiResponse[UserUsage]:
        return success_response(
            status=status.HTTP_200_OK,
            message="Usage retrieved",
            data=UserUsage(
                expires_at=current_user.expires_at,
                worldnews_calls_used=current_user.worldnews_calls_used,
                worldnews_calls_limit=current_user.worldnews_calls_limit,
                llm_tokens_in_used=current_user.llm_tokens_in_used,
                llm_tokens_out_used=current_user.llm_tokens_out_used,
                llm_tokens_limit=current_user.llm_tokens_limit,
            ),
        )

    ### Register function not implemented.

    return router
