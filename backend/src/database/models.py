from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class UserRole(str, Enum):
    """User role enumeration."""

    ADMIN = "admin"
    USER = "user"


class MessageType(str, Enum):
    """Message type enumeration."""

    USER = "user"
    AI = "ai"


# 1. Le modèle de la table DB
class User(SQLModel, table=True):
    """User model representing a user in the database.

    Attributes:
        id: Unique identifier for the user (auto-generated primary key).
        email: User's email address (must be unique and indexed).
        hashed_password: bcrypt-hashed password for secure storage.
        role: User role (admin or user). Defaults to 'user'.

    Example:
        >>> user = User(email="test@test.com", hashed_password="$2b$...", role=UserRole.USER)
        >>> print(user.email)
        test@test.com
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str = Field()
    role: UserRole = Field(default=UserRole.USER, index=True)


class Message(SQLModel, table=True):
    """Message model representing a message in a chat session.

    Attributes:
        id: Unique identifier for the message (auto-generated primary key).
        chat_id: Foreign key referencing the chat to which the message belongs.
        content: The content of the message.
        timestamp: The timestamp when the message was created.

    Example:
        >>> message = Message(chat_id=1, content="Hello, world!", timestamp="2023-01-01T00:00:00Z")
        >>> print(message.content)
        Hello, world!
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    chat_id: int = Field(foreign_key="chat.id")
    type: MessageType = Field(default=MessageType.USER)
    content: str = Field()
    timestamp: str = Field()


class Chat(SQLModel, table=True):
    """Chat model representing a chat session in the database.

    Attributes:
        id: Unique identifier for the chat (auto-generated primary key).
        user_id: Foreign key referencing the user who owns the chat.
        title: Optional title for the chat session.

    Example:
        >>> chat = Chat(user_id=1, title="My First Chat")
        >>> print(chat.title)
        My First Chat
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    date: str = Field(default=None)
    messages: list[Message] = Relationship()


class PressReview(SQLModel, table=True):
    """PressReviews model representing a press review in the database.

    Attributes:
        id: Unique identifier for the press review (auto-generated primary key).
        title: The title of the press review.
        content: The content of the press review.
        date: The date when the press review was published.

    Example:
        >>> review = PressReviews(title="Great News!", content="This is a great news article.", date="2023-01-01")
        >>> print(review.title)
        Great News!
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str = Field()
    description: str = Field()
    content: str = Field()
