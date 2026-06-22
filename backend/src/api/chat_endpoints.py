import asyncio
import logging
from datetime import datetime, timezone
from typing import Annotated

from agents import Runner
from fastapi import APIRouter, Body, Depends, HTTPException, status

from api.models import (
    ApiResponse,
    ChatArticle,
    ChatPublic,
    ChatReviewPublic,
    GenerateReviewRequest,
    MessagePublic,
    SendMessageRequest,
    SendMessageResponse,
    success_response,
)
from core.agent.context import ChatRunContext
from core.agent.search_agent import chat_agent, generate_instructions
from core.auth import verify_user
from core.config import LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT_SECONDS
from core.observability import InferenceTrace, tracing_context
from core.llm_provider import (
    compact_history_if_needed,
)
from core.rag.indexer import build_index_and_retrieve
from database.crud import (
    create_chat_sync,
    create_message_sync,
    get_chat_by_id_sync,
    get_chats_by_user_sync,
    get_messages_by_chat_sync,
    update_chat_loaded_articles_sync,
    update_chat_press_review_sync,
    update_chat_system_prompt_sync,
)
from database.models import MessageType, User
from utils.utils import LLMMessage, sanitize_text

logger = logging.getLogger(__name__)


async def _process_message(chat_id: int, content: str) -> SendMessageResponse:
    """Load history, compact if needed, call LLM, persist both messages."""
    now = datetime.now(timezone.utc).isoformat()
    trace = InferenceTrace.start("chat_turn")

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

    run_context = ChatRunContext(chat_id=chat_id)

    with tracing_context(session_id=str(chat_id)):
        try:
            result = await asyncio.wait_for(
                Runner.run(active_agent, input=openai_messages, context=run_context),
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
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="LLM request timed out",
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
        finally:
            trace.flush(chat_id=chat_id)

    # Fusionner les articles collectés avec les existants (dédupliqués par URL)
    if run_context.loaded_articles:
        existing: list[dict] = chat.loaded_articles or []
        existing_urls = {a.get("url") for a in existing if a.get("url")}
        merged = existing + [
            a for a in run_context.loaded_articles if a["url"] not in existing_urls
        ]
        await asyncio.to_thread(update_chat_loaded_articles_sync, chat_id, merged)

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


def _article_rag_block(a: dict) -> str:
    """Format a loaded_article dict as a Markdown context block for the press review LLM."""
    authors = a.get("authors") or []
    authors_str = ", ".join(authors) if authors else ""
    header = (
        f"**Titre** : {a['title']}\n"
        f"**URL** : {a['url']}\n"
        + (f"**Date** : {a['publish_date']}\n" if a.get("publish_date") else "")
        + (f"**Auteur(s)** : {authors_str}\n" if authors_str else "")
        + (f"**Catégorie** : {a['category']}\n" if a.get("category") else "")
    )
    return header + f"\n{a.get('summary', '')}"


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

    @router.get("/chats/{chat_id}/articles")
    def get_chat_articles(
        chat_id: int,
        current_user: Annotated[User, Depends(verify_user)],
    ) -> ApiResponse[list[ChatArticle]]:
        """Return the deduplicated list of articles loaded during a chat."""
        chat = get_chat_by_id_sync(chat_id)
        if not chat or chat.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
            )
        seen: set[str] = set()
        articles: list[ChatArticle] = []
        for a in chat.loaded_articles or []:
            url = a.get("url", "")
            if url and url not in seen:
                seen.add(url)
                articles.append(ChatArticle(title=a.get("title", ""), url=url))
        return success_response(
            status=status.HTTP_200_OK,
            message="Articles retrieved",
            data=articles,
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

    @router.post("/chats/{chat_id}/review", status_code=status.HTTP_201_CREATED)
    async def generate_chat_review(
        chat_id: int,
        current_user: Annotated[User, Depends(verify_user)],
        body: GenerateReviewRequest = Body(default_factory=GenerateReviewRequest),
    ) -> ApiResponse[ChatReviewPublic]:
        """Generate a press review from the chat's message history."""
        from agents import Runner
        from core.agent.press_review_agent import press_review_agent

        chat = await asyncio.to_thread(get_chat_by_id_sync, chat_id)
        if not chat or chat.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
            )

        messages = await asyncio.to_thread(get_messages_by_chat_sync, chat_id)
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No messages to generate a review from",
            )

        trace = InferenceTrace.start("press_review")

        llm_messages = [
            {
                "role": "user" if m.type == MessageType.USER else "assistant",
                "content": m.content,
            }
            for m in messages
            if m.content
        ]

        # RAG : enrichir le contexte avec les articles sémantiquement pertinents.
        # On injecte dans les instructions de l'agent (clone) plutôt qu'en message
        # system séparé pour éviter "System message must be at the beginning".
        all_articles: list[dict] = chat.loaded_articles or []
        active_review_agent = press_review_agent
        base_instructions = press_review_agent.instructions(None, press_review_agent)

        # Mode article unique : l'utilisateur a sélectionné un article précis
        if body.article_url:
            selected = [a for a in all_articles if a.get("url") == body.article_url]
            if not selected:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Article URL not found in chat loaded articles",
                )
            article = selected[0]
            # Injecte le contenu complet de l'article (stocké dans le champ "summary"
            # par tools.py qui préfère article.text à article.summary)
            rag_block = "## CONTENU COMPLET DE L'ARTICLE\n\n" + _article_rag_block(
                article
            )
            active_review_agent = press_review_agent.clone(
                instructions=base_instructions
                + (
                    f"\n\n## Mode : analyse mono-article\n\n"
                    f"L'utilisateur a sélectionné UN SEUL article : **{article['title']}**.\n\n"
                    f"IMPÉRATIF SCHÉMA : le champ `articles` doit contenir EXACTEMENT UN ArticleSummary "
                    f"pour cet article. NE PAS créer plusieurs ArticleSummary. "
                    f"Tous les paragraphes d'analyse vont dans le champ `content` de ce SEUL objet, "
                    f"séparés par des lignes vides (\\n\\n).\n\n"
                    f"Le champ `content` doit contenir AU MINIMUM 4 paragraphes substantiels "
                    f"qui exploitent intégralement le contenu ci-dessous. "
                    f"Ne pas résumer — analyser en profondeur.\n\n"
                )
                + rag_block
            )
        else:
            # Mode classique : RAG sur tous les articles
            articles = all_articles

            if articles:
                user_msgs = [m["content"] for m in llm_messages if m["role"] == "user"]
                query = " ".join(user_msgs[-3:])
                relevant = await asyncio.to_thread(
                    build_index_and_retrieve, articles, query, top_k=5
                )
                if relevant:
                    rag_block = "\n\n---\n\n".join(
                        _article_rag_block(a) for a in relevant
                    )
                    active_review_agent = press_review_agent.clone(
                        instructions=base_instructions
                        + (
                            "\n\n## Contenu des articles à analyser\n\n"
                            "Voici le contenu complet des articles pertinents issus de la conversation. "
                            "Produis une analyse approfondie de chacun.\n\n"
                            f"{rag_block}"
                        )
                    )

        with tracing_context(session_id=str(chat_id)):
            try:
                result = await asyncio.wait_for(
                    Runner.run(active_review_agent, input=llm_messages),
                    timeout=LLM_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                logger.error("[review] LLM timeout — chat_id=%s", chat_id)
                raise HTTPException(status_code=504, detail="LLM request timed out")
            except Exception as exc:
                logger.error(
                    "[review] LLM provider error — chat_id=%s exc=%r", chat_id, exc
                )
                raise HTTPException(status_code=502, detail="LLM provider error")
            finally:
                trace.flush(chat_id=chat_id, articles_count=len(all_articles))

        output = result.final_output
        if output is None:
            raise HTTPException(
                status_code=502, detail="LLM returned an empty response"
            )

        articles_json = output.model_dump_json()
        now = datetime.now(timezone.utc).isoformat()

        await asyncio.to_thread(
            update_chat_press_review_sync,
            chat_id,
            output.title,
            output.editorial,
            articles_json,
            now,
        )

        return success_response(
            status=status.HTTP_201_CREATED,
            message="Press review generated",
            data=ChatReviewPublic(
                id=chat_id,
                title=output.title,
                description=output.editorial,
                content=articles_json,
                chat_id=chat_id,
                date=now,
            ),
        )

    return router
