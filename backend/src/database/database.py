from pathlib import Path
import os
import sys

from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from sqlmodel import Session, create_engine, select

from core.config import (
    APP_ENV,
    DATABASE_URL,
    DEFAULT_USER_CREDENTIALS,
    DEFAULT_USER_EMAIL,
    SEED_DEFAULT_USER,
    SQL_ECHO,
)
from core.security import hash_password
from database.models import User

# load_dotenv() loads a .env file if present (local dev), but never overrides
# variables already set in the environment (production, Railway, CI, etc.).
load_dotenv()

if not DATABASE_URL:
    if os.getenv("PYTEST_VERSION"):
        DATABASE_URL = "sqlite://"
    else:
        raise ValueError("DATABASE_URL environment variable is not set.")

print(f"Using database URL: {DATABASE_URL}")
engine = create_engine(DATABASE_URL, echo=SQL_ECHO, pool_pre_ping=True)


def _get_alembic_ini_path() -> Path:
    """Resolve path to alembic.ini, robust to different calling contexts.

    Works from src/database/database.py (parents[2]) or via sys.path.
    """
    db_dir = Path(__file__).resolve().parent
    backend_root = db_dir.parents[1]
    alembic_ini = backend_root / "alembic.ini"
    if alembic_ini.exists():
        return alembic_ini
    raise FileNotFoundError(f"alembic.ini not found at {alembic_ini}")


def run_migrations() -> None:
    """Apply pending Alembic migrations to the database.

    Raises:
        FileNotFoundError: If alembic.ini is not found.
        Exception: If migration fails.
    """
    try:
        alembic_ini_path = _get_alembic_ini_path()
        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        print(
            f"✗ Migration failed: {e}",
            file=sys.stderr,
        )
        raise


class Database:
    def __init__(self):
        self.engine = engine

    def init_db(self):
        run_migrations()
        print("Database migrations applied successfully")

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
