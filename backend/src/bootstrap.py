#!/usr/bin/env python
"""
DB init + admin bootstrap script for production and local dev.

This script always applies pending Alembic migrations first, then optionally
creates an admin user if credentials are provided. It is idempotent and safe
to run multiple times.

Usage:
    # Migrations only (no admin creation):
    uv run src/bootstrap.py

    # Via env vars (Railway/production):
    uv run src/bootstrap.py

    # Via CLI args (local/manual):
    uv run src/bootstrap.py --email admin@example.com --password secret123

Environment Variables:
    ADMIN_EMAIL: Email for admin account (optional)
    ADMIN_PASSWORD: Password for admin account (optional)
    DATABASE_URL: Database connection string (required)

Exit Codes:
    0: Success (migrations applied; admin created or skipped)
    1: Error (DB connection failed, migration failed, etc.)
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from sqlmodel import Session, create_engine, select

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config import ADMIN_EMAIL, ADMIN_PASSWORD, DATABASE_URL
from core.security import hash_password
from database.database import run_migrations
from database.models import User, UserRole


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
    Always runs migrations first, then optionally creates the admin user.
    """
    parser = argparse.ArgumentParser(
        description="DB init + one-shot admin bootstrap for production and local dev",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Migrations only (no admin creation):
    uv run src/bootstrap.py

  Via environment variables (production/Railway):
    export ADMIN_EMAIL=admin@example.com
    export ADMIN_PASSWORD=<your-password>
    uv run src/bootstrap.py

  Via CLI arguments (local/manual):
    uv run src/bootstrap.py --email admin@example.com --password <your-password>
        """,
    )

    parser.add_argument(
        "--email",
        help="Admin email address (overrides ADMIN_EMAIL env var)",
    )
    parser.add_argument(
        "--password",
        help="Admin password (overrides ADMIN_PASSWORD env var)",
    )

    args = parser.parse_args()

    # Load .env if present (local development)
    load_dotenv()

    if not DATABASE_URL:
        print(
            "✗ Error: DATABASE_URL environment variable is not set.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Always run migrations first (local dev + production)
    print("📦 Applying database migrations...")
    try:
        run_migrations()
        print("✓ Migrations applied")
    except Exception as e:
        print(f"✗ Migration failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Admin creation is optional: only if credentials are provided
    email = args.email or ADMIN_EMAIL
    password = args.password or ADMIN_PASSWORD

    if not email or not password:
        print("ℹ No admin credentials provided, skipping admin bootstrap")
        sys.exit(0)

    print("🚀 Starting admin bootstrap...")
    success = bootstrap_admin(email, password)

    if not success:
        sys.exit(1)

    print("✓ Bootstrap completed successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
