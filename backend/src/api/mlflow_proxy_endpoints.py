"""
Reverse proxy vers le service MLflow interne Railway.

Accessible uniquement quand MLFLOW_TRACKING_URI et les credentials proxy
sont configurés. Authentification HTTP Basic (compatible navigateur) :
le browser envoie les credentials automatiquement pour tous les assets
après la première authentification.

Routes couvertes :
  /mlflow[/{path}]          → entrée UI + sous-chemins
  /static-files/{path}      → assets SPA MLflow (chemins absolus)
  /ajax-api/{path}          → API REST MLflow (chemins absolus)
  /api/2.0/{path}           → API REST MLflow alternative
"""

import secrets
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from core.config import (
    MLFLOW_PROXY_PASSWORD,
    MLFLOW_PROXY_USERNAME,
    MLFLOW_TRACKING_URI,
)

MLFLOW_INTERNAL_URL = "http://mlflow.railway.internal:5000"

_security = HTTPBasic()

# Headers hop-by-hop à ne pas forwarder
_HOP_BY_HOP = frozenset(
    {"connection", "transfer-encoding", "te", "trailer", "upgrade", "keep-alive"}
)


def _verify_proxy_auth(
    credentials: Annotated[HTTPBasicCredentials, Depends(_security)],
) -> str:
    ok_user = secrets.compare_digest(
        credentials.username.encode(), MLFLOW_PROXY_USERNAME.encode()
    )
    ok_pass = secrets.compare_digest(
        credentials.password.encode(), MLFLOW_PROXY_PASSWORD.encode()
    )
    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=401,
            detail="Accès refusé",
            headers={"WWW-Authenticate": 'Basic realm="MLflow"'},
        )
    return credentials.username


async def _forward(request: Request, target_path: str) -> Response:
    url = f"{MLFLOW_INTERNAL_URL}/{target_path.lstrip('/')}"
    if request.url.query:
        url = f"{url}?{request.url.query}"

    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP | {"host", "authorization"}
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=await request.body(),
            follow_redirects=False,
        )

    resp_headers = {
        k: v for k, v in resp.headers.items() if k.lower() not in _HOP_BY_HOP
    }
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=resp_headers,
    )


def build_mlflow_proxy_router() -> APIRouter | None:
    """Retourne None si MLflow ou les credentials proxy ne sont pas configurés."""
    if (
        not MLFLOW_TRACKING_URI
        or not MLFLOW_PROXY_USERNAME
        or not MLFLOW_PROXY_PASSWORD
    ):
        return None

    router = APIRouter(dependencies=[Depends(_verify_proxy_auth)])

    @router.api_route(
        "/mlflow",
        methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
    )
    async def mlflow_root(request: Request) -> Response:
        return await _forward(request, "")

    @router.api_route(
        "/mlflow/{path:path}",
        methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
    )
    async def mlflow_path(request: Request, path: str) -> Response:
        return await _forward(request, path)

    @router.api_route(
        "/static-files/{path:path}",
        methods=["GET", "HEAD"],
    )
    async def mlflow_static(request: Request, path: str) -> Response:
        return await _forward(request, f"static-files/{path}")

    @router.api_route(
        "/ajax-api/{path:path}",
        methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    )
    async def mlflow_ajax_api(request: Request, path: str) -> Response:
        return await _forward(request, f"ajax-api/{path}")

    @router.api_route(
        "/api/2.0/{path:path}",
        methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    )
    async def mlflow_api_v2(request: Request, path: str) -> Response:
        return await _forward(request, f"api/2.0/{path}")

    return router
