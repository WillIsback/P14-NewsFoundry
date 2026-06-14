"""
Reset script — wipes the database and recreates the schema.

Usage:
    uv run scripts/reset.py                  (local dev)
    python scripts/reset.py                  (Railway console / Docker)

Steps:
  1. Alembic downgrade to base  (drops all tables via migration history)
  2. Drop orphaned PostgreSQL enum types
  3. Alembic upgrade to head    (recreates schema)
  4. Seed with fixture data      (delegates to scripts/seed.py::seed())
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

# ---------------------------------------------------------------------------
# Confirmation prompt (works in both dev and production)
# ---------------------------------------------------------------------------
ENVIRONMENT = __import__("os").environ.get("ENVIRONMENT", "development")
answer = input(
    f"⚠  This will DESTROY all data in the {ENVIRONMENT!r} database and re-seed it.\n"
    "   Type 'yes' to continue: "
).strip()
if answer.lower() != "yes":
    print("Aborted.")
    sys.exit(0)

# ---------------------------------------------------------------------------
# Alembic programmatic API
# ---------------------------------------------------------------------------
from alembic import command as alembic_command  # noqa: E402
from alembic.config import Config as AlembicConfig  # noqa: E402

alembic_cfg = AlembicConfig(str(BACKEND_ROOT / "alembic.ini"))
# Keep the script_location absolute so it works from any cwd
alembic_cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))

print("\n[1/3] Dropping all tables (alembic downgrade base) …")
alembic_command.downgrade(alembic_cfg, "base")
print("      Done.")

# ---------------------------------------------------------------------------
# Drop any PostgreSQL enum types that migrations may have left behind.
# Alembic does not always clean these up on downgrade (e.g. when the DB is
# already at base but a previous run crashed mid-flight).
# ---------------------------------------------------------------------------
print("[1b]  Dropping orphaned enum types …")
import os  # noqa: E402

from sqlalchemy import create_engine as _create_engine  # noqa: E402
from sqlalchemy import text  # noqa: E402

_db_url = os.environ["DATABASE_URL"]
_engine = _create_engine(_db_url)
_ENUM_TYPES = ("messagetype", "userrole")
with _engine.connect() as _conn:
    for _enum in _ENUM_TYPES:
        _conn.execute(text(f"DROP TYPE IF EXISTS {_enum} CASCADE"))
    _conn.commit()
_engine.dispose()
print("      Done.")

print("[2/3] Recreating schema (alembic upgrade head) …")
alembic_command.upgrade(alembic_cfg, "head")
print("      Done.")

# ---------------------------------------------------------------------------
# Re-seed
# ---------------------------------------------------------------------------
print("[3/3] Seeding …")
# Import here so that env.py path setup above is already in effect
sys.path.insert(0, str(BACKEND_ROOT / "scripts"))
from seed import seed  # noqa: E402

seed()
print("\nReset complete.")
