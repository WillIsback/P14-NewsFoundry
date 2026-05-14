from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from core.llm_provider import ContextWindowInfo

DataT = TypeVar("DataT")


class ApiError(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ApiResponse(BaseModel, Generic[DataT]):
    success: bool
    status: int
    message: str
    data: DataT | None = None
    error: ApiError | None = None


class AccessTokenData(BaseModel):
    access_token: str
    token_type: str
    email: str


class MessageData(BaseModel):
    message: str


class UserPublic(BaseModel):
    id: int
    email: str


class UserCreate(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str = Field(
        ...,
        min_length=3,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    password: str


# ---------------------------------------------------------------------------
# Chat / Message
# ---------------------------------------------------------------------------


class ChatPublic(BaseModel):
    id: int
    date: str


class MessagePublic(BaseModel):
    id: int
    chat_id: int
    type: str  # "user" | "ai"
    content: str
    timestamp: str


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


class SendMessageResponse(BaseModel):
    chat_id: int
    message: MessagePublic
    context: ContextWindowInfo


# ---------------------------------------------------------------------------
# Press Review
# ---------------------------------------------------------------------------


class ReviewPublic(BaseModel):
    id: int
    title: str
    description: str
    content: str


class CreateReviewRequest(BaseModel):
    articles: str = Field(min_length=1, max_length=32000)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def success_response(
    *,
    status: int,
    message: str,
    data: DataT | None = None,
) -> ApiResponse[DataT]:
    return ApiResponse[DataT](
        success=True,
        status=status,
        message=message,
        data=data,
        error=None,
    )


def error_response(
    *,
    status: int,
    code: str,
    message: str,
    details: Any | None = None,
) -> ApiResponse[None]:
    return ApiResponse[None](
        success=False,
        status=status,
        message=message,
        data=None,
        error=ApiError(code=code, message=message, details=details),
    )
