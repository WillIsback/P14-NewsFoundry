"""
Centralized configuration for the NewsFoundry backend application.
Manages environment variables, API settings, authentication, and CORS.
"""

import os
from typing import cast, Literal
from dotenv import load_dotenv

# Load .env in local/dev contexts before reading any env variables.
load_dotenv()

# Environment
ENVIRONMENT: Literal["development", "testing", "production"] = cast(
    Literal["development", "testing", "production"],
    os.getenv("ENVIRONMENT", "development"),
)
DEBUG_MODE = ENVIRONMENT in ("development", "testing")

# API Configuration
API_V1_PREFIX = "/api/v1"
API_RATE_LIMIT_REQUESTS = int(os.getenv("API_RATE_LIMIT_REQUESTS", "100"))
API_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("API_RATE_LIMIT_WINDOW_SECONDS", "60"))
API_LOGIN_RATE_LIMIT_REQUESTS = int(os.getenv("API_LOGIN_RATE_LIMIT_REQUESTS", "5"))
API_LOGIN_RATE_LIMIT_WINDOW_SECONDS = int(
    os.getenv("API_LOGIN_RATE_LIMIT_WINDOW_SECONDS", "60")
)
API_AUTH_REQUIRED_PATHS = [
    path.strip()
    for path in os.getenv(
        "API_AUTH_REQUIRED_PATHS",
        f"{API_V1_PREFIX}/auth/protected,{API_V1_PREFIX}/auth/users/me",
    ).split(",")
    if path.strip()
]
TRUSTED_HOSTS = [host.strip() for host in os.getenv("TRUSTED_HOSTS", "*").split(",")]
ENABLE_HTTPS_REDIRECT = os.getenv("ENABLE_HTTPS_REDIRECT", "false").lower() == "true"


# Authentication
SECRET_KEY: str = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# CORS
_cors_raw = os.getenv("CORS_ORIGINS", "")
CORS_ORIGINS: list[str] = (
    [o.strip() for o in _cors_raw.split(",") if o.strip()] if _cors_raw else ["*"]
)

# Database
DATABASE_URL = os.getenv("DATABASE_URL")
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"
APP_ENV = os.getenv("APP_ENV", "development").lower()
SEED_DEFAULT_USER = os.getenv("SEED_DEFAULT_USER", "false").lower() == "true"
DEFAULT_USER_EMAIL: str | None = os.getenv("DEFAULT_USER_EMAIL")
DEFAULT_USER_CREDENTIALS: str | None = os.getenv("DEFAULT_USER_PASSWORD")

# LLM Provider
LLM_BASE_URL: str | None = os.getenv("LLM_BASE_URL")  # e.g. http://localhost:8000/v1
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "EMPTY")
LLM_MODEL: str = os.getenv("LLM_MODEL", "default")
LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
LLM_MAX_CONCURRENT: int = int(os.getenv("LLM_MAX_CONCURRENT", "5"))
LLM_MAX_INPUT_CHARS: int = int(os.getenv("LLM_MAX_INPUT_CHARS", "8000"))
LLM_CONTEXT_WINDOW_TOKENS: int = int(os.getenv("LLM_CONTEXT_WINDOW_TOKENS", "36000"))
# Trigger compaction when history reaches this fraction of the context window (0.0–1.0)
LLM_COMPACT_THRESHOLD_RATIO: float = float(
    os.getenv("LLM_COMPACT_THRESHOLD_RATIO", "0.80")
)
# Number of recent messages to preserve verbatim during compaction
LLM_COMPACT_RECENT_KEEP: int = int(os.getenv("LLM_COMPACT_RECENT_KEEP", "6"))

# Bootstrap Configuration (one-shot admin creation)
BOOTSTRAP_ENABLED = os.getenv("BOOTSTRAP_ENABLED", "false").lower() == "true"
ADMIN_EMAIL: str | None = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD: str | None = os.getenv("ADMIN_PASSWORD")
CI = os.getenv("CI", "false").lower() == "true"


def validate_runtime_config() -> list[str]:
    """Return a list of missing environment variables for runtime startup."""
    missing_vars: list[str] = []

    # Required for application runtime (except during pytest where sqlite is used).
    if not DATABASE_URL and not os.getenv("PYTEST_VERSION"):
        missing_vars.append("DATABASE_URL")

    # If default user seeding is enabled, credentials must be fully configured.
    if SEED_DEFAULT_USER:
        if not DEFAULT_USER_EMAIL:
            missing_vars.append("DEFAULT_USER_EMAIL")
        if not DEFAULT_USER_CREDENTIALS:
            missing_vars.append("DEFAULT_USER_PASSWORD")

    # If bootstrap is enabled, admin credentials are mandatory.
    if BOOTSTRAP_ENABLED:
        if not ADMIN_EMAIL:
            missing_vars.append("ADMIN_EMAIL")
        if not ADMIN_PASSWORD:
            missing_vars.append("ADMIN_PASSWORD")

    # SECRET_KEY must always be explicitly set
    if not SECRET_KEY and not os.getenv("PYTEST_VERSION"):
        missing_vars.append("SECRET_KEY")
    elif ENVIRONMENT == "production" and len(SECRET_KEY) < 32:
        missing_vars.append("SECRET_KEY (too short, must be >= 32 chars in production)")

    # In production, CORS must be explicitly restricted
    cors_env = os.getenv("CORS_ORIGINS", "")
    if ENVIRONMENT == "production" and (not cors_env or "*" in cors_env):
        missing_vars.append(
            "CORS_ORIGINS (wildcard '*' not allowed in production; set explicit origins)"
        )

    return missing_vars
