from datetime import datetime, timezone
from typing import Annotated

import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.models import (
    ApiResponse,
    CreateReviewRequest,
    ReviewPublic,
    success_response,
)
from core.auth import verify_user
from core.llm_provider import LLMMessage, LLMStructuredRequest, call_llm_structured
from core.prompts import PRESS_REVIEW_PROMPT
from database.crud import (
    create_press_review_sync,
    get_press_reviews_by_user_sync,
)
from database.models import User


class _PressReviewLLMOutput(BaseModel):
    """Structured output schema for the LLM press review generation."""

    title: str = Field(description="Concise, informative title for the press review")
    content: str = Field(
        description="Full press review body formatted in Markdown (## headings, bullet points, **bold** key terms)"
    )


def build_review_router() -> APIRouter:
    router = APIRouter(tags=["review"])

    @router.get("/reviews")
    def get_reviews(
        current_user: Annotated[User, Depends(verify_user)],
    ) -> ApiResponse[list[ReviewPublic]]:
        reviews = get_press_reviews_by_user_sync(current_user.id)  # type: ignore[arg-type]
        return success_response(
            status=status.HTTP_200_OK,
            message="Reviews retrieved",
            data=[
                ReviewPublic(
                    id=r.id,  # type: ignore[arg-type]
                    title=r.title,
                    description=r.description,
                    content=r.content,
                )
                for r in reviews
            ],
        )

    @router.post(
        "/reviews",
        status_code=status.HTTP_201_CREATED,
        responses={
            504: {"description": "LLM request timed out"},
            502: {"description": "LLM provider error"},
        },
    )
    async def create_review(
        body: CreateReviewRequest,
        current_user: Annotated[User, Depends(verify_user)],
    ) -> ApiResponse[ReviewPublic]:
        """Generate a press review via structured LLM output and persist it."""
        try:
            llm_output = await call_llm_structured(
                LLMStructuredRequest(
                    system_prompt=PRESS_REVIEW_PROMPT,
                    messages=[LLMMessage(role="user", content=body.articles)],
                ),
                schema=_PressReviewLLMOutput,
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="LLM request timed out")
        except Exception:
            raise HTTPException(status_code=502, detail="LLM provider error")

        # description = ISO 8601 datetime without timezone suffix (matches frontend format)
        description = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        review = await asyncio.to_thread(
            create_press_review_sync,
            current_user.id,  # type: ignore[arg-type]
            llm_output.title,
            description,
            llm_output.content,
        )

        return success_response(
            status=status.HTTP_201_CREATED,
            message="Press review created",
            data=ReviewPublic(
                id=review.id,  # type: ignore[arg-type]
                title=review.title,
                description=review.description,
                content=review.content,
            ),
        )

    return router
