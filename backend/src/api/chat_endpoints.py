import asyncio
import logging
from datetime import datetime, timezone
from typing import Annotated

from agents import Runner
from fastapi import APIRouter, Depends, HTTPException, status

from api.models import (
    ApiResponse,
    ChatPublic,
    MessagePublic,
    SendMessageRequest,
    SendMessageResponse,
    success_response,
)
from core.agent.search_agent import chat_agent, generate_instructions
from core.auth import verify_user
from core.config import LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT_SECONDS
from core.llm_provider import (
    compact_history_if_needed,
)
from database.crud import (
    create_chat_sync,
    create_message_sync,
    get_chat_by_id_sync,
    get_chats_by_user_sync,
    get_messages_by_chat_sync,
    update_chat_system_prompt_sync,
)
from database.models import MessageType, User
from utils.utils import LLMMessage, sanitize_text

logger = logging.getLogger(__name__)


async def _process_message(chat_id: int, content: str) -> SendMessageResponse:
    """Load history, compact if needed, call LLM, persist both messages."""
    now = datetime.now(timezone.utc).isoformat()

    # Ensure the chat has a frozen system prompt (generated on first message).
    # Using the stored prompt guarantees conversation continuity across days.
    chat = await asyncio.to_thread(get_chat_by_id_sync, chat_id)
    if chat and not chat.system_prompt:
        frozen_prompt = generate_instructions()
        await asyncio.to_thread(update_chat_system_prompt_sync, chat_id, frozen_prompt)
        agent_instructions = frozen_prompt
    else:
        agent_instructions = chat.system_prompt if chat else generate_instructions()

    active_agent = chat_agent.clone(instructions=agent_instructions)

    history = await asyncio.to_thread(get_messages_by_chat_sync, chat_id)
    llm_messages = [
        LLMMessage(
            role="user" if m.type == MessageType.USER else "assistant",
            content=m.content,
        )
        for m in history
        if m.content  # skip messages with empty content (e.g. failed LLM responses)
    ]
    # Validate/sanitize user content
    try:
        sanitized_content = sanitize_text(content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    llm_messages.append(LLMMessage(role="user", content=sanitized_content))

    # Persist the user message BEFORE calling the LLM, so it survives a timeout,
    # a client disconnect (CancelledError), or an LLM error — the chat is never
    # left empty and the user's query is never lost.
    await asyncio.to_thread(
        create_message_sync,
        chat_id,
        sanitized_content,
        now,
        MessageType.USER,
    )

    llm_messages, ctx_info = await compact_history_if_needed(llm_messages)

    # Build the input list in the OpenAI messages format expected by the Agents SDK.
    # The agent's own system prompt (instructions) is injected by the SDK automatically;
    # we only pass the conversation history here.
    openai_messages = [{"role": m.role, "content": m.content} for m in llm_messages]

    try:
        result = await asyncio.wait_for(
            Runner.run(active_agent, input=openai_messages),
            timeout=LLM_TIMEOUT_SECONDS,
        )
        response_content = result.final_output
    except asyncio.TimeoutError:
        logger.error(
            "[chat] LLM timeout after %.1fs — chat_id=%s base_url=%s model=%s",
            LLM_TIMEOUT_SECONDS,
            chat_id,
            LLM_BASE_URL,
            LLM_MODEL,
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="LLM request timed out"
        )
    except Exception as exc:
        logger.error(
            "[chat] LLM provider error — chat_id=%s exc=%r base_url=%s model=%s",
            chat_id,
            exc,
            LLM_BASE_URL,
            LLM_MODEL,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="LLM provider error"
        )

    # Persist AI response (the user message was already persisted before the LLM call)
    ai_timestamp = datetime.now(timezone.utc).isoformat()
    ai_msg = await asyncio.to_thread(
        create_message_sync,
        chat_id,
        response_content,
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

    @router.post("/chats/{chat_id}/messages")
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
