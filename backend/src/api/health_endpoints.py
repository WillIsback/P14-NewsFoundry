"""Health check endpoint for production observability.

GET /api/v1/health — vérifie la connectivité DB, LLM et la configuration
courante. Retourne un statut global "ok" | "degraded" | "error" avec le
détail de chaque sous-système.

Utilisé par :
- Le smoke test CI post-déploiement Railway
- Le monitoring Vercel / Railway pour valider qu'une mise en prod est saine
- Le wet_test_endpoints.py (section 0 — Santé infra)
"""

from __future__ import annotations

import asyncio
import logging
import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from core.config import (
    ENVIRONMENT,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_TIMEOUT_SECONDS,
    WORLDNEWS_MOCK,
)
from core.llm_client import build_llm_client

logger = logging.getLogger(__name__)

# Timeout court pour le health check — on ne veut pas bloquer le smoke test
_HEALTH_LLM_TIMEOUT = min(10.0, LLM_TIMEOUT_SECONDS)


async def _check_db() -> dict:
    """Tente une requête SQL triviale pour valider la connectivité DB."""
    try:
        from database.database import engine
        from sqlalchemy import text

        def _ping():
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        await asyncio.to_thread(_ping)
        return {"status": "ok"}
    except Exception as exc:
        logger.error("[health] DB check failed: %s", exc)
        return {"status": "error", "detail": str(exc)}


async def _check_llm() -> dict:
    """Envoie un appel /models au LLM provider pour valider la connectivité réseau.

    On utilise l'endpoint /models (lecture seule, pas de token LLM consommé)
    plutôt qu'un vrai chat/completion.
    """
    if not LLM_BASE_URL:
        return {"status": "error", "detail": "LLM_BASE_URL not configured"}

    try:
        client = build_llm_client()
        t0 = time.monotonic()
        models = await asyncio.wait_for(
            client.models.list(), timeout=_HEALTH_LLM_TIMEOUT
        )
        latency_ms = int((time.monotonic() - t0) * 1000)
        model_ids = [m.id for m in models.data]
        configured_model_present = LLM_MODEL in model_ids
        return {
            "status": "ok" if configured_model_present else "degraded",
            "latency_ms": latency_ms,
            "base_url": LLM_BASE_URL,
            "configured_model": LLM_MODEL,
            "model_available": configured_model_present,
            "available_models": model_ids,
        }
    except asyncio.TimeoutError:
        logger.error(
            "[health] LLM check timed out after %ss — base_url=%s",
            _HEALTH_LLM_TIMEOUT,
            LLM_BASE_URL,
        )
        return {
            "status": "error",
            "detail": f"timeout after {_HEALTH_LLM_TIMEOUT}s",
            "base_url": LLM_BASE_URL,
        }
    except Exception as exc:
        logger.error("[health] LLM check failed: %s — base_url=%s", exc, LLM_BASE_URL)
        return {
            "status": "error",
            "detail": str(exc),
            "base_url": LLM_BASE_URL,
        }


def build_health_router() -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    async def health_check():
        """Check connectivity to DB, LLM provider, and report current config.

        Returns HTTP 200 with status "ok" when all systems are healthy.
        Returns HTTP 503 with status "degraded" or "error" otherwise.
        This endpoint is intentionally unauthenticated so CI smoke tests can
        hit it without a valid token.
        """
        db_result, llm_result = await asyncio.gather(
            _check_db(),
            _check_llm(),
        )

        statuses = {db_result["status"], llm_result["status"]}
        if "error" in statuses:
            overall = "error"
        elif "degraded" in statuses:
            overall = "degraded"
        else:
            overall = "ok"

        payload = {
            "status": overall,
            "environment": ENVIRONMENT,
            "worldnews_mock": WORLDNEWS_MOCK,
            "subsystems": {
                "db": db_result,
                "llm": llm_result,
            },
        }

        http_status = 200 if overall == "ok" else 503
        if overall != "ok":
            logger.warning("[health] overall=%s payload=%s", overall, payload)

        return JSONResponse(content=payload, status_code=http_status)

    return router
