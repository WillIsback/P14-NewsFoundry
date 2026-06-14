"""Factory partagée pour le client AsyncOpenAI.

Quand ``LLM_PROXY_URL`` est défini (ex. proxy HTTP sortant de Tailscale dans
le conteneur), les appels LLM sont routés au travers ; sinon ils sont directs.
Le proxy est volontairement scopé aux seuls appels LLM — l'egress
WorldNewsAPI/Sentry n'est pas affecté.
"""

from __future__ import annotations

import httpx
from openai import AsyncOpenAI
from types import EllipsisType

from core.config import LLM_API_KEY, LLM_BASE_URL, LLM_PROXY_URL


def build_llm_client(proxy_url: str | None | EllipsisType = ...) -> AsyncOpenAI:
    """Construit un AsyncOpenAI, proxifié si un proxy est configuré.

    proxy_url=... (sentinelle) → lit ``LLM_PROXY_URL`` depuis la config.
    Passer explicitement ``None`` force l'absence de proxy.

    Le ``AsyncOpenAI`` retourné est propriétaire du ``httpx.AsyncClient`` créé ;
    l'appelant est responsable de fermer le client ``AsyncOpenAI`` (ce qui ferme
    le client httpx sous-jacent).
    """
    if proxy_url is ...:
        proxy_url = LLM_PROXY_URL

    # Configuration anti-hang : Désactivation stricte du Keep-Alive
    # indispensable pour éviter les blocages (TCP blackholes) via le SOCKS5 userspace Tailscale.
    http_client = httpx.AsyncClient(
        proxy=proxy_url if proxy_url else None,
        timeout=120.0,  # Un timeout généreux pour les longues générations
        limits=httpx.Limits(max_keepalive_connections=0, keepalive_expiry=0.0),
        headers={"Connection": "close"},
    )

    return AsyncOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        http_client=http_client,
    )
