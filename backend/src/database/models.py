from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    """User role enumeration."""

    ADMIN = "admin"
    USER = "user"


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

    id: Optional[int] = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str = Field()
    role: UserRole = Field(default=UserRole.USER, index=True)

