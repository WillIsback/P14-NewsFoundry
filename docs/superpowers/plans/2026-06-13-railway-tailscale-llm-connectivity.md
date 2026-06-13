# In-Container Tailscale LLM Connectivity — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Railway backend reach the private vLLM over Tailscale by embedding the official Tailscale client in the backend container and routing LLM calls through a local HTTP proxy.

**Architecture:** `tailscaled` runs inside the backend container in userspace mode (non-root) and exposes a local outbound HTTP proxy on `localhost:1055`. A shared `AsyncOpenAI` factory routes LLM/health calls through that proxy when `LLM_PROXY_URL` is set; all other egress stays direct. vLLM stays fully private on the tailnet.

**Tech Stack:** Python 3.13, FastAPI, openai SDK (`AsyncOpenAI`), httpx, Tailscale (`tailscaled` userspace + outbound HTTP proxy), Docker (multi-stage), uv.

All paths below are relative to the repo root. The backend lives under `backend/`.

---

## File Structure

- `backend/src/core/llm_client.py` — **new.** Shared factory `build_llm_client()` returning an `AsyncOpenAI` wired with an optional proxy. Single source of truth for LLM client construction.
- `backend/src/core/config.py` — **modify.** Add `LLM_PROXY_URL` env read.
- `backend/src/core/llm_provider.py` — **modify.** Replace inline `AsyncOpenAI(...)` with `build_llm_client()`.
- `backend/src/api/health_endpoints.py` — **modify.** Replace inline `AsyncOpenAI(...)` with `build_llm_client()`.
- `backend/pyproject.toml` — **modify.** Add `httpx` to runtime dependencies.
- `backend/tests/test_llm_client.py` — **new.** Unit tests for the factory.
- `backend/docker-entrypoint.sh` — **new.** Starts `tailscaled` + `tailscale up`, then execs the app.
- `backend/Dockerfile` — **modify.** Copy Tailscale binaries, create state dir, switch `CMD` to the entrypoint.

---

## Task 1: Shared LLM client factory + config

**Files:**
- Modify: `backend/src/core/config.py`
- Create: `backend/src/core/llm_client.py`
- Test: `backend/tests/test_llm_client.py`

- [ ] **Step 1: Add `LLM_PROXY_URL` to config**

In `backend/src/core/config.py`, directly after the existing line `LLM_MODEL: str = os.getenv("LLM_MODEL", "default")` (around line 68), add:

```python
# Optional local proxy for LLM egress (e.g. http://localhost:1055 — Tailscale
# outbound HTTP proxy inside the container). Empty in dev/CI → direct calls.
LLM_PROXY_URL: str | None = os.getenv("LLM_PROXY_URL")
```

- [ ] **Step 2: Write the failing test**

Create `backend/tests/test_llm_client.py`:

```python
from unittest.mock import MagicMock, patch

import core.llm_client as llm_client


def test_build_llm_client_uses_proxy_when_url_provided():
    with (
        patch.object(llm_client, "httpx") as mock_httpx,
        patch.object(llm_client, "AsyncOpenAI") as mock_openai,
    ):
        fake_http_client = MagicMock()
        mock_httpx.AsyncClient.return_value = fake_http_client

        llm_client.build_llm_client(proxy_url="http://localhost:1055")

        mock_httpx.AsyncClient.assert_called_once_with(proxy="http://localhost:1055")
        _, kwargs = mock_openai.call_args
        assert kwargs["http_client"] is fake_http_client


def test_build_llm_client_no_proxy_when_url_empty():
    with (
        patch.object(llm_client, "httpx") as mock_httpx,
        patch.object(llm_client, "AsyncOpenAI") as mock_openai,
    ):
        llm_client.build_llm_client(proxy_url=None)

        mock_httpx.AsyncClient.assert_not_called()
        _, kwargs = mock_openai.call_args
        assert kwargs["http_client"] is None


def test_build_llm_client_defaults_to_config_proxy():
    with (
        patch.object(llm_client, "LLM_PROXY_URL", "http://localhost:1055"),
        patch.object(llm_client, "httpx") as mock_httpx,
        patch.object(llm_client, "AsyncOpenAI") as mock_openai,
    ):
        fake_http_client = MagicMock()
        mock_httpx.AsyncClient.return_value = fake_http_client

        llm_client.build_llm_client()  # no arg → reads LLM_PROXY_URL

        mock_httpx.AsyncClient.assert_called_once_with(proxy="http://localhost:1055")
        _, kwargs = mock_openai.call_args
        assert kwargs["http_client"] is fake_http_client
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_llm_client.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.llm_client'`.

- [ ] **Step 4: Write minimal implementation**

Create `backend/src/core/llm_client.py`:

```python
"""Factory partagée pour le client AsyncOpenAI.

Quand ``LLM_PROXY_URL`` est défini (ex. proxy HTTP sortant de Tailscale dans
le conteneur), les appels LLM sont routés au travers ; sinon ils sont directs.
Le proxy est volontairement scopé aux seuls appels LLM — l'egress
WorldNewsAPI/Sentry n'est pas affecté.
"""

from __future__ import annotations

import httpx
from openai import AsyncOpenAI

from core.config import LLM_API_KEY, LLM_BASE_URL, LLM_PROXY_URL


def build_llm_client(proxy_url: str | None = ...) -> AsyncOpenAI:
    """Construit un AsyncOpenAI, proxifié si un proxy est configuré.

    proxy_url=... (sentinelle) → lit ``LLM_PROXY_URL`` depuis la config.
    Passer explicitement ``None`` force l'absence de proxy.
    """
    if proxy_url is ...:
        proxy_url = LLM_PROXY_URL

    http_client = httpx.AsyncClient(proxy=proxy_url) if proxy_url else None
    return AsyncOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        http_client=http_client,
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_llm_client.py -v`
Expected: PASS (3 passed).

- [ ] **Step 6: Commit**

```bash
git add backend/src/core/config.py backend/src/core/llm_client.py backend/tests/test_llm_client.py
git commit -m "feat(llm): add shared AsyncOpenAI factory with optional proxy"
```

---

## Task 2: Wire the factory into provider and health check

**Files:**
- Modify: `backend/src/core/llm_provider.py:37-40`
- Modify: `backend/src/api/health_endpoints.py` (the `_check_llm` client construction, ~line 65)

- [ ] **Step 1: Replace the inline client in `llm_provider.py`**

In `backend/src/core/llm_provider.py`, change the import block and the client singleton.

Replace the existing import line `from openai import AsyncOpenAI` with:

```python
from core.llm_client import build_llm_client
```

Replace the existing singleton (lines 37-40):

```python
_client = AsyncOpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
)
```

with:

```python
_client = build_llm_client()
```

Then remove now-unused imports of `LLM_API_KEY` and `LLM_BASE_URL` from the `from core.config import (...)` block **only if** they are no longer referenced elsewhere in the file. Verify with:

Run: `cd backend && grep -nE "LLM_API_KEY|LLM_BASE_URL" src/core/llm_provider.py`
If the only remaining hits were the deleted lines, drop them from the import; otherwise leave the import as-is.

- [ ] **Step 2: Replace the inline client in `health_endpoints.py`**

In `backend/src/api/health_endpoints.py`, inside `_check_llm`, replace:

```python
        client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
```

with:

```python
        client = build_llm_client()
```

Add the import near the other imports (after `from openai import AsyncOpenAI`):

```python
from core.llm_client import build_llm_client
```

Leave the existing `from openai import AsyncOpenAI` import in place only if still used; if `AsyncOpenAI` is no longer referenced after this change, remove that import. Verify with:

Run: `cd backend && grep -nE "AsyncOpenAI" src/api/health_endpoints.py`
Remove the `from openai import AsyncOpenAI` line if there are no other references.

- [ ] **Step 3: Run the full test suite**

Run: `cd backend && ENVIRONMENT=testing CI=true uv run pytest tests/ -q`
Expected: all tests pass (the suite mocks the LLM; `LLM_PROXY_URL` is unset in CI → `http_client=None`, behaviour unchanged).

- [ ] **Step 4: Lint**

Run: `cd backend && uv run ruff check src/ tests/`
Expected: no errors (fix unused-import warnings if `ruff` flags leftover imports).

- [ ] **Step 5: Commit**

```bash
git add backend/src/core/llm_provider.py backend/src/api/health_endpoints.py
git commit -m "refactor(llm): route provider and health client through factory"
```

---

## Task 3: Add httpx as a runtime dependency

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/uv.lock` (regenerated)

- [ ] **Step 1: Add httpx to runtime dependencies**

In `backend/pyproject.toml`, inside the `[project] dependencies = [ ... ]` list, add a new entry (keep alphabetical-ish ordering near the other clients):

```python
    "httpx>=0.28.1",
```

Rationale: `core/llm_client.py` imports `httpx` directly and the runtime image is built with `uv sync --no-dev`. It must not rely on the transitive dependency from `openai`.

- [ ] **Step 2: Regenerate the lock file**

Run: `cd backend && uv sync`
Expected: `Resolved … packages`, lock updated. `httpx` now appears as a direct project dependency.

- [ ] **Step 3: Verify the runtime install would include httpx**

Run: `cd backend && uv sync --no-dev --frozen 2>&1 | tail -3`
Expected: succeeds (no "frozen" mismatch), httpx present.

- [ ] **Step 4: Restore the dev environment**

Run: `cd backend && uv sync`
Expected: dev deps reinstalled (pytest etc.).

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock
git commit -m "build(backend): add httpx as a direct runtime dependency"
```

---

## Task 4: Embed Tailscale in the backend container

**Files:**
- Create: `backend/docker-entrypoint.sh`
- Modify: `backend/Dockerfile`

- [ ] **Step 1: Determine the Tailscale version to pin**

Run: `curl -s https://api.github.com/repos/tailscale/tailscale/releases/latest | grep -oE '"tag_name": *"v[0-9.]+"'`
Expected: e.g. `"tag_name": "v1.86.2"`.
Note the version **without** the leading `v` (e.g. `1.86.2`). Use it as `TAILSCALE_VERSION` in Step 3. If the command fails, browse https://tailscale.com/changelog and use the latest stable.

- [ ] **Step 2: Create the entrypoint script**

Create `backend/docker-entrypoint.sh`:

```sh
#!/bin/sh
set -e

# Dev/CI fallback: without an auth key, skip Tailscale and run the app directly.
if [ -z "$TS_AUTHKEY" ]; then
  echo "[entrypoint] TS_AUTHKEY not set — skipping Tailscale, starting app directly"
  exec python src/main.py
fi

TS_SOCKET=/app/.tailscale/tailscaled.sock
TS_STATEDIR=/app/.tailscale

echo "[entrypoint] starting tailscaled (userspace networking)…"
tailscaled \
  --tun=userspace-networking \
  --outbound-http-proxy-listen=localhost:1055 \
  --statedir="$TS_STATEDIR" \
  --socket="$TS_SOCKET" &

echo "[entrypoint] bringing tailscale up…"
# `tailscale up` blocks until the node is authenticated and Running; with
# `set -e`, an auth failure aborts the container (visible failed deploy).
tailscale --socket="$TS_SOCKET" up \
  --authkey="$TS_AUTHKEY" \
  --hostname="${TS_HOSTNAME:-newsfoundry-backend}"

echo "[entrypoint] tailnet up — starting app"
exec python src/main.py
```

- [ ] **Step 3: Modify the Dockerfile**

In `backend/Dockerfile`, add the Tailscale binaries, the state dir, and the entrypoint. Make the following three edits to the **runtime stage** (Stage 2).

(a) Immediately after the `FROM python:3.13-slim-bookworm` line, add the version arg and copy the binaries from the official image (replace `1.86.2` with the value from Step 1):

```dockerfile
# Tailscale binaries (pinned) — copied from the official image
ARG TAILSCALE_VERSION=1.86.2
COPY --from=tailscale/tailscale:v${TAILSCALE_VERSION} \
  /usr/local/bin/tailscaled /usr/local/bin/tailscale /usr/local/bin/
```

(b) After the existing `COPY --chown=appuser:appuser src/ ./src/` line, create the writable Tailscale state dir and copy the entrypoint:

```dockerfile
# Writable state/socket dir for tailscaled running as non-root appuser
RUN mkdir -p /app/.tailscale && chown appuser:appuser /app/.tailscale

COPY --chown=appuser:appuser docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh
```

(c) Replace the final `CMD ["python", "src/main.py"]` line with:

```dockerfile
CMD ["./docker-entrypoint.sh"]
```

- [ ] **Step 4: Build the image locally to verify it assembles**

Run: `cd backend && docker build -t newsfoundry-backend:tailscale-test .`
Expected: build succeeds, including the `COPY --from=tailscale/tailscale:v1.86.2` stage.

- [ ] **Step 5: Verify the dev/CI fallback path (no TS_AUTHKEY)**

Run:
```bash
docker run --rm -e ENVIRONMENT=testing newsfoundry-backend:tailscale-test \
  timeout 3 ./docker-entrypoint.sh 2>&1 | grep -m1 'skipping Tailscale'
```
Expected: prints `[entrypoint] TS_AUTHKEY not set — skipping Tailscale, starting app directly` (the app may then fail to boot without a DB — fine; we only assert the fallback branch is taken, and `timeout 3` stops it).

- [ ] **Step 6: Commit**

```bash
git add backend/Dockerfile backend/docker-entrypoint.sh
git commit -m "build(backend): embed Tailscale userspace client in container"
```

---

## Manual actions (outside the repo — performed by the operator)

These are **not** code and are not committed. Do them before/at deploy time.

1. **Tailscale ACL (admin console → Access Controls):**
   - Define an ownable tag, e.g.:
     ```json
     "tagOwners": { "tag:railway": ["autogroup:admin"] }
     ```
   - Allow the Railway node to reach vLLM only:
     ```json
     { "action": "accept", "src": ["tag:railway"], "dst": ["100.70.22.24:30000"] }
     ```
2. **Auth key (admin console → Settings → Keys):** generate a key that is
   **Ephemeral + Reusable + Tagged `tag:railway`**. Copy it.
3. **Railway backend service → Variables:**
   - `TS_AUTHKEY` = the key from step 2 (mark as secret)
   - `LLM_PROXY_URL` = `http://localhost:1055`
   - confirm `LLM_BASE_URL` = `http://100.70.22.24:30000/v1` (unchanged)
4. **`railway-tailscale` service:** already decommissioned ✅ (done).

---

## Post-deploy verification

- [ ] After Railway redeploys, run from a tailnet machine:
  `tailscale status | grep newsfoundry-backend`
  Expected: the backend node appears (ephemeral, online).
- [ ] Probe the health endpoint:
  `curl -s -w '\nHTTP %{http_code}\n' https://p14-newsfoundry-production.up.railway.app/api/v1/health`
  Expected: HTTP 200, JSON `status: "ok"`, `subsystems.llm.status: "ok"`, `subsystems.db.status: "ok"`.

---

## Out of scope (separate follow-up)

The `wet-test` CI job still has a **deploy-race** bug: it runs immediately on push to `main` while Railway deploys asynchronously, so it can hit the previous deployment. Fix separately by polling `GET /api/v1/health` with retries (wait for the new deployment) before running assertions. Not part of this plan.
