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

# Demo Account (distinct from SEED_DEFAULT_USER which is reserved for CI/CD)
DEMO_USER_EMAIL: str | None = os.getenv("DEMO_USER_EMAIL")
DEMO_USER_PASSWORD: str | None = os.getenv("DEMO_USER_PASSWORD")
DEMO_ACCOUNT_EXPIRES_DAYS: int = int(os.getenv("DEMO_ACCOUNT_EXPIRES_DAYS", "30"))
DEMO_WORLDNEWS_LIMIT: int | None = (
    int(os.getenv("DEMO_WORLDNEWS_LIMIT"))
    if os.getenv("DEMO_WORLDNEWS_LIMIT")
    else None
)
DEMO_LLM_TOKENS_LIMIT: int = int(os.getenv("DEMO_LLM_TOKENS_LIMIT", "10000000"))

# WorldNewsAPI
WORLDNEWSAPI_KEY: str = os.getenv("WORLDNEWSAPI_KEY", "")
# En mode mock (ENVIRONMENT != "production"), retourne des données fixes
# pour éviter d'atteindre le rate-limit pendant le développement local.
WORLDNEWS_MOCK: bool = os.getenv("ENVIRONMENT", "development") != "production"

# LLM Provider
LLM_BASE_URL: str | None = os.getenv("LLM_BASE_URL")  # e.g. http://localhost:8000/v1
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "EMPTY")
LLM_MODEL: str = os.getenv("LLM_MODEL", "default")
# Optional local proxy for LLM egress (e.g. http://localhost:1055 — Tailscale
# outbound HTTP proxy inside the container). Empty in dev/CI → direct calls.
LLM_PROXY_URL: str | None = os.getenv("LLM_PROXY_URL")
LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
LLM_MAX_CONCURRENT: int = int(os.getenv("LLM_MAX_CONCURRENT", "5"))
# Bound the agent's generation to stay resilient under shared-GPU contention.
# 4096 pour absorber une revue de presse structurée complète (10+ articles).
AGENT_MAX_TOKENS: int = int(os.getenv("AGENT_MAX_TOKENS", "4096"))
# Number of top-news clusters returned to the agent (smaller = shorter context/output).
TOP_NEWS_CLUSTERS: int = int(os.getenv("TOP_NEWS_CLUSTERS", "5"))
LLM_MAX_INPUT_CHARS: int = int(os.getenv("LLM_MAX_INPUT_CHARS", "8000"))
LLM_CONTEXT_WINDOW_TOKENS: int = int(os.getenv("LLM_CONTEXT_WINDOW_TOKENS", "36000"))
# Trigger compaction when history reaches this fraction of the context window (0.0–1.0)
LLM_COMPACT_THRESHOLD_RATIO: float = float(
    os.getenv("LLM_COMPACT_THRESHOLD_RATIO", "0.80")
)
# Number of recent messages to preserve verbatim during compaction
LLM_COMPACT_RECENT_KEEP: int = int(os.getenv("LLM_COMPACT_RECENT_KEEP", "6"))

# Observability / MLflow
# Si absent ou vide, le tracking MLflow est désactivé (mode no-op silencieux).
MLFLOW_TRACKING_URI: str | None = os.getenv("MLFLOW_TRACKING_URI") or None

# Bootstrap Configuration (one-shot admin creation)
BOOTSTRAP_ENABLED = os.getenv("BOOTSTRAP_ENABLED", "false").lower() == "true"
ADMIN_EMAIL: str | None = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD: str | None = os.getenv("ADMIN_PASSWORD")
CI = os.getenv("CI", "false").lower() == "true"


def _check_seeding_config(missing_vars: list[str]) -> None:
    """Validate default-user seeding variables when seeding is enabled."""
    if not SEED_DEFAULT_USER:
        return
    if not DEFAULT_USER_EMAIL:
        missing_vars.append("DEFAULT_USER_EMAIL")
    if not DEFAULT_USER_CREDENTIALS:
        missing_vars.append("DEFAULT_USER_PASSWORD")


def _check_bootstrap_config(missing_vars: list[str]) -> None:
    """Validate admin bootstrap variables when bootstrap is enabled."""
    if not BOOTSTRAP_ENABLED:
        return
    if not ADMIN_EMAIL:
        missing_vars.append("ADMIN_EMAIL")
    if not ADMIN_PASSWORD:
        missing_vars.append("ADMIN_PASSWORD")


def _check_secret_key(missing_vars: list[str]) -> None:
    """Validate SECRET_KEY presence and strength."""
    if ENVIRONMENT != "testing" and not SECRET_KEY:
        missing_vars.append("SECRET_KEY")
    elif ENVIRONMENT == "production" and len(SECRET_KEY) < 32:
        missing_vars.append("SECRET_KEY (too short, must be >= 32 chars in production)")


def _check_cors_config(missing_vars: list[str]) -> None:
    """Validate that CORS_ORIGINS is explicitly restricted in production."""
    cors_env = os.getenv("CORS_ORIGINS", "")
    if ENVIRONMENT == "production" and (not cors_env or "*" in cors_env):
        missing_vars.append(
            "CORS_ORIGINS (wildcard '*' not allowed in production; set explicit origins)"
        )


def validate_runtime_config() -> list[str]:
    """Return a list of missing environment variables for runtime startup."""
    missing_vars: list[str] = []

    # Required for application runtime (except during pytest where sqlite is used).
    if not DATABASE_URL and not os.getenv("PYTEST_VERSION"):
        missing_vars.append("DATABASE_URL")

    _check_seeding_config(missing_vars)
    _check_bootstrap_config(missing_vars)
    _check_secret_key(missing_vars)
    _check_cors_config(missing_vars)

    return missing_vars
