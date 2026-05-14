"""Wet (integration) tests — hit the running API server end-to-end.

Usage:
    # From backend/ directory
    uv run python tests/wet_test_endpoints.py

Environment variables (all optional — defaults match local dev):
    BASE_URL         — server base URL (default: http://localhost:8000)
    TEST_EMAIL       — login email      (default: test@test.com)
    TEST_PASSWORD    — login password   (default: test)

Exit code: 0 if all tests pass, 1 if any fail.
"""

from __future__ import annotations

import os
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Resolve backend/src so we can import config for defaults if needed.
BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
TEST_EMAIL = os.getenv("DEFAULT_USER_EMAIL", os.getenv("TEST_EMAIL", "test@test.com"))
TEST_PASSWORD = os.getenv("DEFAULT_USER_PASSWORD", os.getenv("TEST_PASSWORD", "test"))

# --- ANSI colours -----------------------------------------------------------

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


# --- Result tracking --------------------------------------------------------


@dataclass
class Results:
    passed: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)

    def ok(self, name: str) -> None:
        print(f"  {GREEN}✔{RESET}  {name}")
        self.passed.append(name)

    def fail(self, name: str, reason: str) -> None:
        print(f"  {RED}✘{RESET}  {name}")
        print(f"       {RED}{reason}{RESET}")
        self.failed.append((name, reason))

    def summary(self) -> int:
        total = len(self.passed) + len(self.failed)
        print()
        print(f"{BOLD}Results: {len(self.passed)}/{total} passed{RESET}")
        for name, reason in self.failed:
            print(f"  {RED}FAIL{RESET} {name}: {reason}")
        return 1 if self.failed else 0


results = Results()


# --- Helper -----------------------------------------------------------------


def assert_status(name: str, response: httpx.Response, expected: int) -> bool:
    if response.status_code != expected:
        results.fail(
            name,
            f"expected HTTP {expected}, got {response.status_code} — {response.text[:200]}",
        )
        return False
    return True


def assert_field(name: str, data: Any, *keys: str) -> bool:
    """Assert that nested keys exist in data (dict path)."""
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            results.fail(name, f"missing field '{'.'.join(keys)}' in response")
            return False
        current = current[key]
    return True


# --- Test sections ----------------------------------------------------------


def section(title: str) -> None:
    print(f"\n{CYAN}{BOLD}▶ {title}{RESET}")


def test_health(client: httpx.Client) -> None:
    section("Health / server reachability")
    name = "GET / returns 200 or 404 (server is up)"
    try:
        r = client.get("/")
        if r.status_code in (200, 404, 422):
            results.ok(name)
        else:
            results.fail(name, f"unexpected status {r.status_code}")
    except httpx.ConnectError as exc:
        results.fail(name, f"cannot connect to {BASE_URL}: {exc}")


def test_auth(client: httpx.Client) -> dict[str, str]:
    """Returns auth headers if login succeeds, else empty dict."""
    section("Authentication")

    # --- Invalid credentials ---
    name = "POST /api/v1/auth/login — wrong password → 401"
    r = client.post("/api/v1/auth/login", json={"email": TEST_EMAIL, "password": "bad"})
    if assert_status(name, r, 401):
        results.ok(name)

    # --- Valid credentials ---
    name = "POST /api/v1/auth/login — valid credentials → 200 + token"
    r = client.post(
        "/api/v1/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if not assert_status(name, r, 200):
        return {}
    body = r.json()
    if not assert_field(name, body, "data", "access_token"):
        return {}
    if not assert_field(name, body, "data", "email"):
        return {}
    results.ok(name)

    token = body["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # --- /protected ---
    name = "GET /api/v1/auth/protected — valid token → 200"
    r = client.get("/api/v1/auth/protected", headers=headers)
    if assert_status(name, r, 200):
        results.ok(name)

    # --- /protected unauthenticated ---
    name = "GET /api/v1/auth/protected — no token → 401"
    r = client.get("/api/v1/auth/protected")
    if assert_status(name, r, 401):
        results.ok(name)

    # --- /users/me ---
    name = "GET /api/v1/auth/users/me → 200 + email matches"
    r = client.get("/api/v1/auth/users/me", headers=headers)
    if assert_status(name, r, 200):
        body = r.json()
        email_in_response = body.get("data", {}).get("email")
        if email_in_response == TEST_EMAIL:
            results.ok(name)
        else:
            results.fail(
                name,
                f"email mismatch: expected {TEST_EMAIL!r}, got {email_in_response!r}",
            )

    return headers


def test_chats(client: httpx.Client, headers: dict[str, str]) -> int | None:
    """Returns the created chat_id or None on failure."""
    section("Chat endpoints")

    # --- Unauthenticated list ---
    name = "GET /api/v1/chats — no token → 401"
    r = client.get("/api/v1/chats")
    if assert_status(name, r, 401):
        results.ok(name)

    # --- List chats (authenticated, may be empty) ---
    name = "GET /api/v1/chats — authenticated → 200"
    r = client.get("/api/v1/chats", headers=headers)
    if not assert_status(name, r, 200):
        return None
    results.ok(name)

    # --- New chat + first message (calls LLM) ---
    name = "POST /api/v1/chats/message — create chat + LLM reply → 201"
    r = client.post(
        "/api/v1/chats/message",
        json={"content": "Bonjour, peux-tu te présenter brièvement?"},
        headers=headers,
        timeout=120,  # LLM may be slow
    )
    if not assert_status(name, r, 201):
        return None
    body = r.json()
    if not assert_field(name, body, "data", "chat_id"):
        return None
    if not assert_field(name, body, "data", "message", "content"):
        return None
    if not assert_field(name, body, "data", "context", "used_tokens"):
        return None
    results.ok(name)

    chat_id: int = body["data"]["chat_id"]

    # --- List messages in new chat ---
    name = f"GET /api/v1/chats/{chat_id}/messages → 200 + ≥2 messages (user+AI)"
    r = client.get(f"/api/v1/chats/{chat_id}/messages", headers=headers)
    if assert_status(name, r, 200):
        msgs = r.json().get("data", [])
        if len(msgs) >= 2:
            results.ok(name)
        else:
            results.fail(name, f"expected ≥2 messages, got {len(msgs)}")

    # --- Continue existing chat ---
    name = f"POST /api/v1/chats/{chat_id}/message — continue chat → 200"
    r = client.post(
        f"/api/v1/chats/{chat_id}/message",
        json={"content": "Quels sont tes domaines de compétence?"},
        headers=headers,
        timeout=120,
    )
    if assert_status(name, r, 200):
        body = r.json()
        if assert_field(name, body, "data", "message", "content"):
            results.ok(name)

    # --- Messages for a chat owned by another user → 404 ---
    name = "GET /api/v1/chats/999999/messages — unknown chat → 404"
    r = client.get("/api/v1/chats/999999/messages", headers=headers)
    if assert_status(name, r, 404):
        results.ok(name)

    return chat_id


def test_reviews(client: httpx.Client, headers: dict[str, str]) -> None:
    section("Press Review endpoints")

    # --- Unauthenticated ---
    name = "GET /api/v1/reviews — no token → 401"
    r = client.get("/api/v1/reviews")
    if assert_status(name, r, 401):
        results.ok(name)

    # --- List reviews (may be empty) ---
    name = "GET /api/v1/reviews — authenticated → 200"
    r = client.get("/api/v1/reviews", headers=headers)
    if not assert_status(name, r, 200):
        return
    results.ok(name)

    # --- Create review (calls LLM structured output) ---
    sample_articles = (
        "Article 1: L'IA générative transforme les rédactions. "
        "Les journaux adoptent des outils d'IA pour accélérer la production de contenu. "
        "Certains craignent une perte de qualité éditoriale.\n\n"
        "Article 2: OpenAI lance GPT-5, son modèle le plus puissant. "
        "Les experts saluent les progrès en raisonnement mais soulèvent des questions éthiques. "
        "Le débat sur la régulation s'intensifie en Europe."
    )
    name = "POST /api/v1/reviews — create press review via LLM → 201"
    r = client.post(
        "/api/v1/reviews",
        json={"articles": sample_articles},
        headers=headers,
        timeout=180,  # structured LLM call may be slow
    )
    if not assert_status(name, r, 201):
        return
    body = r.json()
    if not assert_field(name, body, "data", "id"):
        return
    if not assert_field(name, body, "data", "title"):
        return
    if not assert_field(name, body, "data", "content"):
        return
    results.ok(name)

    # --- List reviews — should contain at least the one just created ---
    name = "GET /api/v1/reviews — after creation → 200 + ≥1 review"
    r = client.get("/api/v1/reviews", headers=headers)
    if assert_status(name, r, 200):
        reviews = r.json().get("data", [])
        if len(reviews) >= 1:
            results.ok(name)
        else:
            results.fail(name, "expected ≥1 review after creation, got 0")

    # --- Invalid payload ---
    name = "POST /api/v1/reviews — empty articles → 422"
    r = client.post(
        "/api/v1/reviews",
        json={"articles": ""},
        headers=headers,
    )
    if assert_status(name, r, 422):
        results.ok(name)


# --- Entry point ------------------------------------------------------------


def main() -> int:
    print(f"{BOLD}NewsFoundry Wet Tests{RESET}")
    print(f"  Server : {CYAN}{BASE_URL}{RESET}")
    print(f"  User   : {TEST_EMAIL}")

    with httpx.Client(base_url=BASE_URL, timeout=30) as client:
        test_health(client)

        headers = test_auth(client)
        if not headers:
            print(
                f"\n{RED}Authentication failed — skipping authenticated tests.{RESET}"
            )
            return results.summary()

        try:
            test_chats(client, headers)
        except Exception:
            results.fail("chat suite", traceback.format_exc())

        try:
            test_reviews(client, headers)
        except Exception:
            results.fail("review suite", traceback.format_exc())

    return results.summary()


if __name__ == "__main__":
    sys.exit(main())
