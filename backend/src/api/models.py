from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


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


class MessageData(BaseModel):
    message: str


class UserPublic(BaseModel):
    id: int
    email: str


class UserCreate(BaseModel):
    email: str
    password: str


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
