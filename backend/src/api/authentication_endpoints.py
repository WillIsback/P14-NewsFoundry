from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlmodel import Session, select

from api.models import (
    AccessTokenData,
    ApiResponse,
    MessageData,
    UserPublic,
    success_response,
)
from core.auth import create_access_token, get_current_user
from core.security import verify_password
from database.database import Database
from database.models import User


def build_authentication_router(db: Database) -> APIRouter:
    router = APIRouter(tags=["authentication"])

    @router.post("/login")
    async def login_for_access_token(
        email: Annotated[str, Form(...)],
        password: Annotated[str, Form(...)],
        session: Annotated[Session, Depends(db.get_db)],
    ) -> ApiResponse[AccessTokenData]:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Identifiant ou mot de passe incorrect",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(data={"sub": user.email})
        return success_response(
            status=status.HTTP_200_OK,
            message="Login successful",
            data=AccessTokenData(access_token=access_token, token_type="bearer"),
        )

    @router.get("/protected")
    async def protected_route(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> ApiResponse[MessageData]:
        return success_response(
            status=status.HTTP_200_OK,
            message="Access granted",
            data=MessageData(
                message=f"Hello, {current_user.email}! This is a protected resource."
            ),
        )

    @router.get("/users/me")
    def read_users_me(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> ApiResponse[UserPublic]:
        return success_response(
            status=status.HTTP_200_OK,
            message="Current user retrieved",
            data=UserPublic(id=current_user.id, email=current_user.email),
        )
    
    ### Register function not implemented.

    return router