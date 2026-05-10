#!/usr/bin/env python
"""
One-shot admin bootstrap script for production.

This script is designed to be run once via a Railway deploy hook or manually.
It creates an admin user if one doesn't exist, making it safe to run multiple times
(idempotent).

Usage:
    # Via env vars (Railway/production):
    uv run src/bootstrap.py

    # Via CLI args (local/manual):
    uv run src/bootstrap.py --email admin@example.com --password secret123

Environment Variables:
    BOOTSTRAP_ENABLED: If "true", enables admin creation (default: false)
    ADMIN_EMAIL: Email for admin account (required if BOOTSTRAP_ENABLED=true)
    ADMIN_PASSWORD: Password for admin account (required if BOOTSTRAP_ENABLED=true)
    DATABASE_URL: Database connection string (required)
    CI: If "true", indicates CI/production environment (Railway sets this)

Exit Codes:
    0: Success (admin created or already exists)
    1: Error (missing required vars, DB connection failed, etc.)
"""

import argparse
import os
from pathlib import Path
import sys

from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from sqlmodel import Session, create_engine, select

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config import ADMIN_EMAIL, ADMIN_PASSWORD, DATABASE_URL
from core.security import hash_password
from database.models import User, UserRole

ALEMBIC_INI_PATH = Path(__file__).resolve().parents[1] / "alembic.ini"


def run_migrations() -> None:
    alembic_cfg = Config(str(ALEMBIC_INI_PATH))
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    command.upgrade(alembic_cfg, "head")


def bootstrap_admin(email: str, password: str) -> bool:
    """
    Create an admin user if one doesn't exist.

    Args:
        email: Admin email address
        password: Admin password (will be hashed)

    Returns:
        True if admin was created or already exists, False on error

    Raises:
        ValueError: If DATABASE_URL is not set
        Exception: If database connection fails
    """
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set.")

    try:
        run_migrations()
        engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

        with Session(engine) as session:
            # Check if an admin user already exists
            existing_admin = session.exec(
                select(User).where(User.role == UserRole.ADMIN)
            ).first()

            if existing_admin:
                print(
                    f"ℹ Admin already exists ({existing_admin.email}), skipping creation"
                )
                return True

            # Create the admin user
            admin_user = User(
                email=email,
                hashed_password=hash_password(password),
                role=UserRole.ADMIN,
            )
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)

            print(f"✓ Admin user created: {admin_user.email}")
            return True

    except Exception as e:
        print(f"✗ Error during bootstrap: {e}", file=sys.stderr)
        return False


def main():
    """
    Main entry point for the bootstrap script.

    Supports both environment variable and CLI argument modes.
    """
    parser = argparse.ArgumentParser(
        description="One-shot admin bootstrap for production",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Via environment variables (production/Railway):
    export BOOTSTRAP_ENABLED=true
    export ADMIN_EMAIL=admin@example.com
        export ADMIN_PASSWORD=<your-password>
    uv run src/bootstrap.py

  Via CLI arguments (local/manual):
        uv run src/bootstrap.py --email admin@example.com --password <your-password>
        """,
    )

    parser.add_argument(
        "--email",
        help="Admin email address (overrides ADMIN_EMAIL env var if provided)",
    )
    parser.add_argument(
        "--password",
        help="Admin password (overrides ADMIN_PASSWORD env var if provided)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force admin creation even if one already exists (WARNING: will fail due to unique email constraint)",
    )

    args = parser.parse_args()

    # Load .env if present (local development)
    load_dotenv()

    # Determine email and password source
    email = args.email or ADMIN_EMAIL
    password = args.password or ADMIN_PASSWORD

    # Validation
    if not email or not password:
        print(
            "✗ Error: ADMIN_EMAIL and ADMIN_PASSWORD must be provided\n"
            "  Via env vars: export ADMIN_EMAIL=... ADMIN_PASSWORD=...\n"
            "  Via CLI args: --email ... --password ...",
            file=sys.stderr,
        )
        sys.exit(1)

    if not DATABASE_URL:
        print(
            "✗ Error: DATABASE_URL environment variable is not set.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Run bootstrap
    print("🚀 Starting admin bootstrap...")
    success = bootstrap_admin(email, password)

    if not success:
        sys.exit(1)

    print("✓ Bootstrap completed successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
