from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from api.models import (
    AccessTokenData,
    ApiResponse,
    LoginRequest,
    MessageData,
    UserPublic,
    success_response,
)
from core.auth import create_access_token, verify_user
from core.security import hash_password, verify_password
from database.database import Database
from database.models import User

# Bcrypt hash of a fixed dummy password. Used to keep comparable verification
# cost when the user does not exist, reducing account-enumeration timing leaks.
DUMMY_BCRYPT_HASH = hash_password("timing-check-placeholder")


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
        current_user: Annotated[User, Depends(verify_user)],
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
        current_user: Annotated[User, Depends(verify_user)],
    ) -> ApiResponse[UserPublic]:
        return success_response(
            status=status.HTTP_200_OK,
            message="Current user retrieved",
            data=UserPublic(id=current_user.id, email=current_user.email),  # type: ignore[arg-type]
        )

    ### Register function not implemented.

    return router
