"""
Seed script — populates the database with realistic fixture data.

Usage:
    uv run scripts/seed.py                  (local dev)
    python scripts/seed.py                  (Railway console / Docker)

Guards:
  - Fully idempotent: safe to run multiple times; existing rows are skipped.
  - Confirmation prompt when ENVIRONMENT=production.

Seeded entities (all linked to test@test.com):
  - 1 User  (test@test.com / test1234)
  - 5 Chats, each with 2 Messages (user turn + AI turn)
  - 5 PressReviews
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure src/ is on the import path regardless of working directory
# ---------------------------------------------------------------------------
BACKEND_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = BACKEND_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# ---------------------------------------------------------------------------
# Now import project modules
# ---------------------------------------------------------------------------
from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_ROOT / ".env")

from core.config import DEFAULT_USER_CREDENTIALS, ENVIRONMENT  # noqa: E402
from core.fixtures import CHATS, PRESS_REVIEWS  # noqa: E402
from core.security import hash_password  # noqa: E402
from database.database import engine  # noqa: E402
from database.models import Chat, Message, PressReview, User, UserRole  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

# ---------------------------------------------------------------------------
# Guard: refuse to seed in production (hardcoded test credentials are
# not suitable for a live environment).
# ---------------------------------------------------------------------------
if ENVIRONMENT == "production":
    print(
        "✗ Refusing to seed: hardcoded credentials not safe in production.",
        file=sys.stderr,
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Fixture data (imported from core.fixtures — single source of truth)
# ---------------------------------------------------------------------------
SEED_EMAIL = "test@test.com"
# Use the configured credential so seed and init_db() always agree.
# Falls back to "test1234" only when the env var is not set (e.g. CI).
SEED_PASSWORD = DEFAULT_USER_CREDENTIALS or "test1234"


# ---------------------------------------------------------------------------
# Seed logic
# ---------------------------------------------------------------------------


def seed() -> None:
    with Session(engine) as session:
        # -- User ----------------------------------------------------------
        user = session.exec(select(User).where(User.email == SEED_EMAIL)).first()
        if not user:
            user = User(
                email=SEED_EMAIL,
                hashed_password=hash_password(SEED_PASSWORD),
                role=UserRole.USER,
            )
            session.add(user)
            session.flush()  # populate user.id before referencing it
            print(f"  + User created: {SEED_EMAIL}")
        else:
            print(f"  ~ User already exists: {SEED_EMAIL} (id={user.id})")

        # -- Chats & Messages ----------------------------------------------
        existing_chat_count = len(
            list(session.exec(select(Chat).where(Chat.user_id == user.id)).all())
        )
        if existing_chat_count >= len(CHATS):
            print(f"  ~ Chats already seeded ({existing_chat_count} found), skipping.")
        else:
            for chat_data in CHATS:
                chat = Chat(user_id=user.id, date=chat_data["date"])
                session.add(chat)
                session.flush()  # populate chat.id
                for msg_data in chat_data["messages"]:
                    session.add(
                        Message(
                            chat_id=chat.id,
                            type=msg_data["type"],
                            content=msg_data["content"],
                            timestamp=msg_data["timestamp"],
                        )
                    )
            print(f"  + {len(CHATS)} chats seeded with 2 messages each.")

        # -- Press Reviews -------------------------------------------------
        existing_review_count = len(
            list(
                session.exec(
                    select(PressReview).where(PressReview.user_id == user.id)
                ).all()
            )
        )
        if existing_review_count >= len(PRESS_REVIEWS):
            print(
                f"  ~ PressReviews already seeded ({existing_review_count} found), skipping."
            )
        else:
            for review_data in PRESS_REVIEWS:
                session.add(
                    PressReview(
                        user_id=user.id,
                        title=review_data["title"],
                        description=review_data["description"],
                        content=review_data["content"],
                    )
                )
            print(f"  + {len(PRESS_REVIEWS)} press reviews seeded.")

        session.commit()


if __name__ == "__main__":
    print(f"Seeding database (ENVIRONMENT={ENVIRONMENT}) …")
    seed()
    print("Done.")
