"""
Centralized configuration for the NewsFoundry backend application.
Manages environment variables, API settings, authentication, and CORS.
"""

import os
from typing import Literal

# Environment
ENVIRONMENT: Literal["development", "testing", "production"] = os.getenv(
    "ENVIRONMENT", "development"
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
SECRET_KEY = os.getenv("SECRET_KEY", "your_super_secret_change_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")
APP_ENV = os.getenv("APP_ENV", "development").lower()
SEED_DEFAULT_USER = os.getenv("SEED_DEFAULT_USER", "false").lower() == "true"
DEFAULT_USER_EMAIL: str | None = os.getenv("DEFAULT_USER_EMAIL")
DEFAULT_USER_CREDENTIALS: str | None = os.getenv("DEFAULT_USER_PASSWORD")

# Bootstrap Configuration (one-shot admin creation)
BOOTSTRAP_ENABLED = os.getenv("BOOTSTRAP_ENABLED", "false").lower() == "true"
ADMIN_EMAIL: str | None = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD: str | None = os.getenv("ADMIN_PASSWORD")
CI = os.getenv("CI", "false").lower() == "true"
