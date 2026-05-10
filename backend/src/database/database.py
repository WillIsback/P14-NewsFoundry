from dotenv import load_dotenv
from sqlmodel import SQLModel, Session, create_engine, select

from core.config import (
    APP_ENV,
    DATABASE_URL,
    DEFAULT_USER_CREDENTIALS,
    DEFAULT_USER_EMAIL,
    SEED_DEFAULT_USER,
)
from core.security import hash_password, verify_password
from database.models import User

# load_dotenv() loads a .env file if present (local dev), but never overrides
# variables already set in the environment (production, Railway, CI, etc.).
load_dotenv()

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

print(f"Using database URL: {DATABASE_URL}")
engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)


class Database:
    def __init__(self):
        self.engine = engine

    def init_db(self):
        SQLModel.metadata.create_all(self.engine)
        print("Database initialized successfully")

        if not SEED_DEFAULT_USER:
            print(f"Skipping default user seed (APP_ENV={APP_ENV})")
            return

        if not DEFAULT_USER_EMAIL or not DEFAULT_USER_CREDENTIALS:
            raise ValueError(
                "SEED_DEFAULT_USER is enabled but DEFAULT_USER_EMAIL or "
                "DEFAULT_USER_PASSWORD environment variable is not set."
            )

        with Session(self.engine) as session:
            user = session.exec(
                select(User).where(User.email == DEFAULT_USER_EMAIL)
            ).first()

            if not user:
                session.add(
                    User(
                        email=DEFAULT_USER_EMAIL,
                        hashed_password=hash_password(DEFAULT_USER_CREDENTIALS),
                    )
                )
                session.commit()
                print(f"Default user created: {DEFAULT_USER_EMAIL}")
            else:
                print(f"Default user already exists: {DEFAULT_USER_EMAIL}")

    def get_db(self):
        """Gère la connexion à la DB (Session)"""
        with Session(self.engine) as session:
            yield session
