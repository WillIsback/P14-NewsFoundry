from fastapi import FastAPI

from api.authentication_endpoints import build_authentication_router
from core.config import API_V1_PREFIX
from database.database import Database


def setup_routers(app: FastAPI, db: Database) -> None:
    """Register all API routers with their respective prefixes."""

    # Authentication endpoints with /api/v1/auth prefix
    auth_router = build_authentication_router(db)
    app.include_router(auth_router, prefix=f"{API_V1_PREFIX}/auth")
