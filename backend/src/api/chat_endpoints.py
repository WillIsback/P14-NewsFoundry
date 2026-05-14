from datetime import datetime, timezone
from typing import Annotated

import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from api.models import (
    ApiResponse,
    ChatPublic,
    MessagePublic,
    SendMessageRequest,
    SendMessageResponse,
    success_response,
)
from core.auth import verify_user
from core.llm_provider import (
    LLMMessage,
    LLMRequest,
    call_llm,
    compact_history_if_needed,
)
from core.prompts import CHAT_PROMPT
from database.crud import (
    create_chat_sync,
    create_message_sync,
    get_chat_by_id_sync,
    get_chats_by_user_sync,
    get_messages_by_chat_sync,
)
from database.models import MessageType, User


async def _process_message(chat_id: int, content: str) -> SendMessageResponse:
    """Load history, compact if needed, call LLM, persist both messages."""
    now = datetime.now(timezone.utc).isoformat()

    history = await asyncio.to_thread(get_messages_by_chat_sync, chat_id)
    llm_messages = [
        LLMMessage(
            role="user" if m.type == MessageType.USER else "assistant",
            content=m.content,
        )
        for m in history
    ]
    # Validate/sanitize user content using LLMMessage validator
    try:
        sanitized_content = LLMMessage(role="user", content=content).content
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    llm_messages.append(LLMMessage(role="user", content=sanitized_content))

    llm_messages, ctx_info = await compact_history_if_needed(llm_messages)

    try:
        llm_response = await call_llm(
            LLMRequest(system_prompt=CHAT_PROMPT, messages=llm_messages)
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="LLM request timed out"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="LLM provider error"
        )

    # Persist user message first (chronological order)
    await asyncio.to_thread(
        create_message_sync,
        chat_id,
        sanitized_content,
        now,
        MessageType.USER,
    )

    # Persist AI response
    ai_timestamp = datetime.now(timezone.utc).isoformat()
    ai_msg = await asyncio.to_thread(
        create_message_sync,
        chat_id,
        llm_response.content,
        ai_timestamp,
        MessageType.AI,
    )

    return SendMessageResponse(
        chat_id=chat_id,
        message=MessagePublic(
            id=ai_msg.id,  # type: ignore[arg-type]
            chat_id=ai_msg.chat_id,
            type=ai_msg.type.value,
            content=ai_msg.content,
            timestamp=ai_msg.timestamp,
        ),
        context=ctx_info,
    )


def build_chat_router() -> APIRouter:
    router = APIRouter(tags=["chat"])

    @router.get("/chats")
    def get_chats(
        current_user: Annotated[User, Depends(verify_user)],
    ) -> ApiResponse[list[ChatPublic]]:
        chats = get_chats_by_user_sync(current_user.id)  # type: ignore[arg-type]
        return success_response(
            status=status.HTTP_200_OK,
            message="Chats retrieved",
            data=[ChatPublic(id=c.id, date=c.date) for c in chats],  # type: ignore[arg-type]
        )

    @router.get("/chats/{chat_id}/messages")
    def get_messages(
        chat_id: int,
        current_user: Annotated[User, Depends(verify_user)],
    ) -> ApiResponse[list[MessagePublic]]:
        chat = get_chat_by_id_sync(chat_id)
        # Return 404 regardless — do not reveal existence to other users
        if not chat or chat.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
            )

        messages = get_messages_by_chat_sync(chat_id)
        return success_response(
            status=status.HTTP_200_OK,
            message="Messages retrieved",
            data=[
                MessagePublic(
                    id=m.id,  # type: ignore[arg-type]
                    chat_id=m.chat_id,
                    type=m.type.value,
                    content=m.content,
                    timestamp=m.timestamp,
                )
                for m in messages
            ],
        )

    @router.post("/chats/message", status_code=status.HTTP_201_CREATED)
    async def new_chat_message(
        body: SendMessageRequest,
        current_user: Annotated[User, Depends(verify_user)],
    ) -> ApiResponse[SendMessageResponse]:
        """Create a new chat and send the first message in a single call."""
        now = datetime.now(timezone.utc).isoformat()
        chat = await asyncio.to_thread(create_chat_sync, current_user.id, now)  # type: ignore[arg-type]
        if chat.id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Chat creation failed",
            )
        data = await _process_message(chat.id, body.content)
        return success_response(
            status=status.HTTP_201_CREATED,
            message="Chat created and message sent",
            data=data,
        )

    @router.post("/chats/{chat_id}/message")
    async def continue_chat_message(
        chat_id: int,
        body: SendMessageRequest,
        current_user: Annotated[User, Depends(verify_user)],
    ) -> ApiResponse[SendMessageResponse]:
        """Send a message to an existing chat session."""
        chat = await asyncio.to_thread(get_chat_by_id_sync, chat_id)
        if not chat or chat.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
            )
        data = await _process_message(chat_id, body.content)
        return success_response(
            status=status.HTTP_200_OK,
            message="Message sent",
            data=data,
        )

    return router
