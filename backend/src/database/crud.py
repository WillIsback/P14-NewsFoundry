from typing import Optional

from sqlmodel import Session, select

from database.models import Chat, Message, MessageType, PressReview, User, UserRole

# Imported here for thread-safe wrappers that open their own Session
from database.database import engine

# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def create_user(
    session: Session,
    email: str,
    hashed_password: str,
    role: UserRole = UserRole.USER,
) -> User:
    user = User(email=email, hashed_password=hashed_password, role=role)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(session: Session, user_id: int) -> bool:
    user = session.get(User, user_id)
    if not user:
        return False
    session.delete(user)
    session.commit()
    return True


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------


def get_chat_by_id(session: Session, chat_id: int) -> Optional[Chat]:
    return session.get(Chat, chat_id)


def get_chats_by_user(session: Session, user_id: int) -> list[Chat]:
    statement = select(Chat).where(Chat.user_id == user_id)
    return list(session.exec(statement).all())


def create_chat(session: Session, user_id: int, date: str) -> Chat:
    chat = Chat(user_id=user_id, date=date)
    session.add(chat)
    session.commit()
    session.refresh(chat)
    return chat


def delete_chat(session: Session, chat_id: int) -> bool:
    chat = session.get(Chat, chat_id)
    if not chat:
        return False
    session.delete(chat)
    session.commit()
    return True


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------


def get_messages_by_chat(session: Session, chat_id: int) -> list[Message]:
    statement = select(Message).where(Message.chat_id == chat_id)
    return list(session.exec(statement).all())


def create_message(
    session: Session,
    chat_id: int,
    content: str,
    timestamp: str,
    type: MessageType = MessageType.USER,
) -> Message:
    message = Message(chat_id=chat_id, content=content, timestamp=timestamp, type=type)
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


# ---------------------------------------------------------------------------
# PressReview
# ---------------------------------------------------------------------------


def get_press_review_by_id(session: Session, review_id: int) -> Optional[PressReview]:
    return session.get(PressReview, review_id)


def get_press_reviews_by_user(session: Session, user_id: int) -> list[PressReview]:
    statement = select(PressReview).where(PressReview.user_id == user_id)
    return list(session.exec(statement).all())


def create_press_review(
    session: Session,
    user_id: int,
    title: str,
    description: str,
    content: str,
) -> PressReview:
    review = PressReview(
        user_id=user_id, title=title, description=description, content=content
    )
    session.add(review)
    session.commit()
    session.refresh(review)
    return review


def delete_press_review(session: Session, review_id: int) -> bool:
    review = session.get(PressReview, review_id)
    if not review:
        return False
    session.delete(review)
    session.commit()
    return True


# ---------------------------------------------------------------------------
# Thread-safe wrappers (open/close their own Session)
# Use these when calling from async code via `asyncio.to_thread()` to avoid
# using a request-scoped Session across await boundaries.
# ---------------------------------------------------------------------------


def get_chat_by_id_sync(chat_id: int) -> Optional[Chat]:
    with Session(engine) as session:
        return get_chat_by_id(session, chat_id)


def get_chats_by_user_sync(user_id: int) -> list[Chat]:
    with Session(engine) as session:
        return get_chats_by_user(session, user_id)


def create_chat_sync(user_id: int, date: str) -> Chat:
    with Session(engine) as session:
        return create_chat(session, user_id=user_id, date=date)


def get_messages_by_chat_sync(chat_id: int) -> list[Message]:
    with Session(engine) as session:
        return get_messages_by_chat(session, chat_id)


def create_message_sync(
    chat_id: int,
    content: str,
    timestamp: str,
    type: MessageType = MessageType.USER,
) -> Message:
    with Session(engine) as session:
        return create_message(
            session, chat_id=chat_id, content=content, timestamp=timestamp, type=type
        )


def get_press_reviews_by_user_sync(user_id: int) -> list[PressReview]:
    with Session(engine) as session:
        return get_press_reviews_by_user(session, user_id)


def create_press_review_sync(
    user_id: int, title: str, description: str, content: str
) -> PressReview:
    with Session(engine) as session:
        return create_press_review(
            session,
            user_id=user_id,
            title=title,
            description=description,
            content=content,
        )
