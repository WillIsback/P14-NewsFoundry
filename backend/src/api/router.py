from fastapi import FastAPI

from api.authentication_endpoints import build_authentication_router
from api.chat_endpoints import build_chat_router
from api.health_endpoints import build_health_router
from api.mlflow_proxy_endpoints import build_mlflow_proxy_router
from api.news_endpoints import build_news_router
from api.review_endpoints import build_review_router
from core.config import API_V1_PREFIX
from database.database import Database


def setup_routers(app: FastAPI, db: Database) -> None:
    """Register all API routers with their respective prefixes."""

    auth_router = build_authentication_router(db)
    app.include_router(auth_router, prefix=f"{API_V1_PREFIX}/auth")

    chat_router = build_chat_router()
    app.include_router(chat_router, prefix=API_V1_PREFIX)

    review_router = build_review_router()
    app.include_router(review_router, prefix=API_V1_PREFIX)

    news_router = build_news_router()
    app.include_router(news_router, prefix=API_V1_PREFIX)

    health_router = build_health_router()
    app.include_router(health_router, prefix=API_V1_PREFIX)

    mlflow_proxy_router = build_mlflow_proxy_router()
    if mlflow_proxy_router is not None:
        app.include_router(mlflow_proxy_router)
