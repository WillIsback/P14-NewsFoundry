"""Endpoints REST pour le pipeline d'ingestion de news."""

import asyncio
import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session

from api.models import ApiResponse, success_response
from core.auth import db as auth_db
from core.auth import verify_user
from core.news.service import fetch_and_build_context
from database.crud import get_top_news_context_by_chat
from database.models import User


class NewsContextRequest(BaseModel):
    chat_id: int
    date: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    source_country: str = Field(default="fr", max_length=2)
    language: str = Field(default="fr", max_length=2)


class NewsContextPublic(BaseModel):
    id: int
    chat_id: int
    date: str
    source_country: str
    language: str
    system_prompt: str
    news: list[dict]
    created_at: str

    model_config = {"from_attributes": True}


logger = logging.getLogger(__name__)


def build_news_router() -> APIRouter:
    router = APIRouter(tags=["news"])

    @router.post("/news/context", status_code=status.HTTP_201_CREATED)
    async def create_news_context(
        body: NewsContextRequest,
        current_user: Annotated[User, Depends(verify_user)],
        session: Annotated[Session, Depends(auth_db.get_db)],
    ) -> ApiResponse[NewsContextPublic]:
        try:
            ctx = await fetch_and_build_context(
                chat_id=body.chat_id,
                source_country=body.source_country,
                language=body.language,
                date=body.date,
                session=session,
            )
        except asyncio.TimeoutError:
            logger.error(
                "[news] timeout fetching news context for chat_id=%s", body.chat_id
            )
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="News fetch timed out",
            )
        except Exception as exc:
            logger.error(
                "[news] error building news context for chat_id=%s: %r",
                body.chat_id,
                exc,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to fetch or build news context",
            )
        return success_response(
            status=status.HTTP_201_CREATED,
            message="News context created",
            data=NewsContextPublic.model_validate(ctx),
        )

    @router.get("/news/context/{chat_id}")
    async def get_news_context(
        chat_id: int,
        current_user: Annotated[User, Depends(verify_user)],
        session: Annotated[Session, Depends(auth_db.get_db)],
    ) -> ApiResponse[NewsContextPublic]:
        ctx = get_top_news_context_by_chat(session, chat_id)
        if not ctx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No news context for this chat",
            )
        return success_response(
            status=status.HTTP_200_OK,
            message="News context retrieved",
            data=NewsContextPublic.model_validate(ctx),
        )

    return router
