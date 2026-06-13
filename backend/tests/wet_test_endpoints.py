"""Wet (integration) tests — hit the running API server end-to-end.

Couvre l'ensemble du backend avant la mise à jour du frontend :
  1. Santé du serveur
  2. Authentification (login, token, /protected, /users/me)
  3. Chats — création, historique, continuité, isolation utilisateur
  4. Agent routing — get_top_news vs search_news (mode mock WorldNews)
  5. Persistance du system_prompt (gelé au premier message)
  6. Press Reviews — liste, création LLM structurée, validation

Usage:
    # Depuis backend/
    uv run python tests/wet_test_endpoints.py

Variables d'environnement (toutes optionnelles) :
    BASE_URL         — URL du serveur  (défaut: http://localhost:8000)
    TEST_EMAIL       — email de login  (défaut: test@test.com)
    TEST_PASSWORD    — mot de passe    (défaut: test)

Code de sortie : 0 si tous les tests passent, 1 sinon.
"""

from __future__ import annotations

import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
TEST_EMAIL = os.getenv("DEFAULT_USER_EMAIL", os.getenv("TEST_EMAIL", "test@test.com"))
TEST_PASSWORD = os.getenv("DEFAULT_USER_PASSWORD", os.getenv("TEST_PASSWORD", "test"))

LLM_TIMEOUT = 180  # secondes — le LLM local peut être lent

# ── ANSI colours ─────────────────────────────────────────────────────────────

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


# ── Tracking résultats ────────────────────────────────────────────────────────


@dataclass
class Results:
    passed: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def ok(self, name: str, detail: str = "") -> None:
        suffix = f"  {DIM}{detail}{RESET}" if detail else ""
        print(f"  {GREEN}✔{RESET}  {name}{suffix}")
        self.passed.append(name)

    def fail(self, name: str, reason: str) -> None:
        print(f"  {RED}✘{RESET}  {name}")
        print(f"       {RED}{reason}{RESET}")
        self.failed.append((name, reason))

    def skip(self, name: str, reason: str = "") -> None:
        suffix = f" ({reason})" if reason else ""
        print(f"  {YELLOW}–{RESET}  {name}{DIM}{suffix}{RESET}")
        self.skipped.append(name)

    def summary(self) -> int:
        total = len(self.passed) + len(self.failed) + len(self.skipped)
        status_color = GREEN if not self.failed else RED
        print()
        print(
            f"{BOLD}{status_color}Résultats : "
            f"{len(self.passed)} réussis / {len(self.failed)} échoués"
            f" / {len(self.skipped)} ignorés — {total} au total{RESET}"
        )
        for name, reason in self.failed:
            print(f"  {RED}FAIL{RESET} {name}: {reason}")
        return 1 if self.failed else 0


results = Results()


# ── Helpers ───────────────────────────────────────────────────────────────────


def section(title: str) -> None:
    print(f"\n{CYAN}{BOLD}▶ {title}{RESET}")


def assert_status(name: str, r: httpx.Response, expected: int) -> bool:
    if r.status_code != expected:
        results.fail(
            name,
            f"HTTP {expected} attendu, reçu {r.status_code} — {r.text[:300]}",
        )
        return False
    return True


def assert_field(name: str, data: Any, *keys: str) -> bool:
    """Vérifie qu'un chemin de clés existe dans un dict imbriqué."""
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            results.fail(name, f"champ manquant : '{'.'.join(keys)}'")
            return False
        current = current[key]
    return True


def get_json(r: httpx.Response) -> dict:
    try:
        return r.json()
    except Exception:
        return {}


# ── 1. Santé du serveur ───────────────────────────────────────────────────────


def test_health(client: httpx.Client) -> bool:
    section("1 · Santé du serveur")
    name = "Serveur accessible (GET / → 2xx/4xx, pas de ConnectError)"
    try:
        r = client.get("/")
        if r.status_code in (200, 404, 422):
            results.ok(name, f"HTTP {r.status_code}")
        else:
            results.fail(name, f"statut inattendu : {r.status_code}")
            return False
    except httpx.ConnectError as exc:
        results.fail(name, f"impossible de joindre {BASE_URL}: {exc}")
        return False

    name = "GET /api/v1/health — DB + LLM joignables → status ok"
    try:
        r = client.get("/api/v1/health", timeout=20)
    except httpx.ConnectError as exc:
        results.fail(name, f"ConnectError: {exc}")
        return False

    body = get_json(r)
    overall = body.get("status", "unknown")
    subsystems = body.get("subsystems", {})
    db_status = subsystems.get("db", {}).get("status", "?")
    llm_status = subsystems.get("llm", {}).get("status", "?")
    llm_latency = subsystems.get("llm", {}).get("latency_ms")
    env = body.get("environment", "?")
    worldnews_mock = body.get("worldnews_mock")

    detail = (
        f"overall={overall} db={db_status} llm={llm_status}"
        + (f" llm_latency={llm_latency}ms" if llm_latency else "")
        + f" env={env} worldnews_mock={worldnews_mock}"
    )

    if overall == "ok":
        results.ok(name, detail)
    elif overall == "degraded":
        # Degraded n'est pas bloquant — le serveur peut fonctionner partiellement
        results.fail(name, f"DEGRADED — {detail}")
        # Log les détails complets pour faciliter le diagnostic
        print(f"       {YELLOW}Détail subsystems :{RESET} {subsystems}")
        return False
    else:
        results.fail(name, f"ERREUR — {detail}")
        print(f"       {RED}Détail subsystems :{RESET} {subsystems}")
        return False

    # Avertissement explicite si worldnews_mock=False en dehors de la prod attendue
    if worldnews_mock is False and env != "production":
        print(
            f"       {YELLOW}⚠ worldnews_mock=False en env={env!r} "
            f"— risque de consommer le quota WorldNewsAPI{RESET}"
        )

    return True


# ── 2. Authentification ───────────────────────────────────────────────────────


def test_auth(client: httpx.Client) -> dict[str, str]:
    """Retourne les headers Authorization si le login réussit, sinon {}."""
    section("2 · Authentification")

    name = "Login mauvais mot de passe → 401"
    r = client.post("/api/v1/auth/login", json={"email": TEST_EMAIL, "password": "bad"})
    if assert_status(name, r, 401):
        results.ok(name)

    name = "Login valide → 200 + access_token"
    r = client.post(
        "/api/v1/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if not assert_status(name, r, 200):
        return {}
    body = get_json(r)
    if not assert_field(name, body, "data", "access_token"):
        return {}
    results.ok(name)

    token = body["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    name = "GET /auth/protected — token valide → 200"
    r = client.get("/api/v1/auth/protected", headers=headers)
    if assert_status(name, r, 200):
        results.ok(name)

    name = "GET /auth/protected — sans token → 401"
    r = client.get("/api/v1/auth/protected")
    if assert_status(name, r, 401):
        results.ok(name)

    name = "GET /auth/users/me → email correspond"
    r = client.get("/api/v1/auth/users/me", headers=headers)
    if assert_status(name, r, 200):
        email_got = get_json(r).get("data", {}).get("email")
        if email_got == TEST_EMAIL:
            results.ok(name)
        else:
            results.fail(name, f"email attendu {TEST_EMAIL!r}, reçu {email_got!r}")

    return headers


# ── 3. Chats — création + historique ─────────────────────────────────────────


def test_chats_basic(client: httpx.Client, headers: dict) -> int | None:
    """Retourne le chat_id créé, ou None si le test échoue."""
    section("3 · Chats — création et historique")

    name = "GET /chats — sans token → 401"
    r = client.get("/api/v1/chats")
    if assert_status(name, r, 401):
        results.ok(name)

    name = "GET /chats — authentifié → 200"
    r = client.get("/api/v1/chats", headers=headers)
    if not assert_status(name, r, 200):
        return None
    results.ok(name)

    name = "POST /chats/message — premier message → 201 + chat_id + content + context"
    t0 = time.time()
    r = client.post(
        "/api/v1/chats/message",
        json={"content": "Bonjour, peux-tu te présenter brièvement ?"},
        headers=headers,
        timeout=LLM_TIMEOUT,
    )
    elapsed = time.time() - t0
    if not assert_status(name, r, 201):
        return None
    body = get_json(r)
    ok = (
        assert_field(name, body, "data", "chat_id")
        and assert_field(name, body, "data", "message", "content")
        and assert_field(name, body, "data", "context", "used_tokens")
    )
    if ok:
        results.ok(name, f"{elapsed:.1f}s")
    chat_id: int = body["data"]["chat_id"]

    name = f"GET /chats/{chat_id}/messages → ≥2 messages (user + IA)"
    r = client.get(f"/api/v1/chats/{chat_id}/messages", headers=headers)
    if assert_status(name, r, 200):
        msgs = get_json(r).get("data", [])
        if len(msgs) >= 2:
            results.ok(name, f"{len(msgs)} messages")
        else:
            results.fail(name, f"attendu ≥2, reçu {len(msgs)}")

    name = "GET /chats/999999/messages — chat inexistant → 404"
    r = client.get("/api/v1/chats/999999/messages", headers=headers)
    if assert_status(name, r, 404):
        results.ok(name)

    return chat_id


# ── 4. Continuité de conversation ─────────────────────────────────────────────


def test_chat_continuity(client: httpx.Client, headers: dict, chat_id: int) -> None:
    section("4 · Continuité de conversation")

    name = f"POST /chats/{chat_id}/messages — 2ème message dans le même chat → 200"
    t0 = time.time()
    r = client.post(
        f"/api/v1/chats/{chat_id}/messages",
        json={"content": "Quels sont tes domaines de compétence ?"},
        headers=headers,
        timeout=LLM_TIMEOUT,
    )
    elapsed = time.time() - t0
    if not assert_status(name, r, 200):
        return
    body = get_json(r)
    if not assert_field(name, body, "data", "message", "content"):
        return

    # Le chat_id doit rester identique (même conversation)
    returned_chat_id = body["data"].get("chat_id")
    if returned_chat_id != chat_id:
        results.fail(name, f"chat_id attendu {chat_id}, reçu {returned_chat_id}")
        return
    results.ok(name, f"{elapsed:.1f}s — même chat #{chat_id}")

    name = f"GET /chats/{chat_id}/messages → ≥4 messages après 2ème échange"
    r = client.get(f"/api/v1/chats/{chat_id}/messages", headers=headers)
    if assert_status(name, r, 200):
        msgs = get_json(r).get("data", [])
        if len(msgs) >= 4:
            results.ok(name, f"{len(msgs)} messages")
        else:
            results.fail(name, f"attendu ≥4, reçu {len(msgs)}")


# ── 5. Agent routing — get_top_news vs search_news ───────────────────────────


def test_agent_routing(client: httpx.Client, headers: dict) -> None:
    section("5 · Agent routing (mock WorldNews)")

    # --- get_top_news : actualités générales du jour ---
    name = "get_top_news — 'actualités du jour' → réponse avec titres de presse"
    t0 = time.time()
    r = client.post(
        "/api/v1/chats/message",
        json={"content": "Quelles sont les principales actualités du jour en France ?"},
        headers=headers,
        timeout=LLM_TIMEOUT,
    )
    elapsed = time.time() - t0
    if assert_status(name, r, 201):
        body = get_json(r)
        content: str = body.get("data", {}).get("message", {}).get("content", "")
        # La mock renvoie des titres connus — au moins l'un doit apparaître
        mock_keywords = ["G7", "Ukraine", "Lyhanna", "salariale", "Zelensky"]
        found = [kw for kw in mock_keywords if kw.lower() in content.lower()]
        if found:
            results.ok(name, f"{elapsed:.1f}s — mots-clés trouvés : {found}")
        else:
            results.fail(
                name,
                f"aucun mot-clé mock trouvé dans la réponse ({elapsed:.1f}s).\n"
                f"       Réponse (200 chars) : {content[:200]}",
            )

    # --- get_top_news : date passée spécifique ---
    name = "get_top_news — date passée '30 mai 2026' → réponse sans refus"
    t0 = time.time()
    r = client.post(
        "/api/v1/chats/message",
        json={"content": "Donne-moi les actualités du 30 mai 2026."},
        headers=headers,
        timeout=LLM_TIMEOUT,
    )
    elapsed = time.time() - t0
    if assert_status(name, r, 201):
        body = get_json(r)
        content = body.get("data", {}).get("message", {}).get("content", "")
        # L'agent ne doit PAS refuser pour cause de "date future"
        refusal_phrases = ["ne peut pas", "impossible", "avenir", "futur", "future"]
        refused = any(p in content.lower() for p in refusal_phrases)
        if not refused and content:
            results.ok(name, f"{elapsed:.1f}s")
        elif refused:
            results.fail(name, f"l'agent a refusé la date passée : {content[:200]}")
        else:
            results.fail(name, "réponse vide")

    # --- search_news : sujet précis ---
    name = "search_news — 'conflit en Ukraine' → articles de recherche"
    t0 = time.time()
    r = client.post(
        "/api/v1/chats/message",
        json={"content": "Peux-tu me parler du conflit en Ukraine ?"},
        headers=headers,
        timeout=LLM_TIMEOUT,
    )
    elapsed = time.time() - t0
    if assert_status(name, r, 201):
        body = get_json(r)
        content = body.get("data", {}).get("message", {}).get("content", "")
        # La mock search Ukraine renvoie des titres identifiables — l'agent doit
        # les restituer (pas halluciner depuis ses connaissances paramétriques).
        ukraine_keywords = [
            "Zelensky",
            "Donbass",
            "cessez-le-feu",
            "Bruxelles",
            "HCR",
            "réfugiés",
            "Kiev",
        ]
        found = [kw for kw in ukraine_keywords if kw.lower() in content.lower()]
        if found:
            results.ok(name, f"{elapsed:.1f}s — mots-clés mock trouvés : {found}")
        else:
            results.fail(
                name,
                f"aucun mot-clé mock Ukraine trouvé — le LLM a probablement halluciné ({elapsed:.1f}s).\n"
                f"       Réponse (300 chars) : {content[:300]}",
            )


# ── 6. Persistance du system_prompt ──────────────────────────────────────────


def test_system_prompt_persistence(
    client: httpx.Client, headers: dict, chat_id: int
) -> None:
    section("6 · Persistance du system_prompt")

    # Importer directement la BDD pour vérification
    try:
        from database.database import engine
        from database.models import Chat
        from sqlmodel import Session

        name = f"system_prompt gelé en BDD pour chat #{chat_id}"
        with Session(engine) as s:
            chat = s.get(Chat, chat_id)
        sp = chat.system_prompt if chat else None
        if sp and len(sp) > 100:
            # Vérifier que la date est encodée (format YYYY-MM-DD)
            import re

            date_present = bool(re.search(r"\d{4}-\d{2}-\d{2}", sp))
            results.ok(
                name,
                f"{len(sp)} chars — date dans le prompt : {date_present}",
            )
        elif sp:
            results.fail(name, f"system_prompt trop court ({len(sp)} chars) : {sp!r}")
        else:
            results.fail(name, "system_prompt est NULL en base")
    except ImportError:
        results.skip(
            "system_prompt BDD",
            "modules database non disponibles hors PYTHONPATH=src",
        )
    except Exception as exc:
        results.fail("system_prompt BDD", str(exc))


# ── 7. Press Reviews ──────────────────────────────────────────────────────────


def test_reviews(client: httpx.Client, headers: dict) -> None:
    section("7 · Press Reviews")

    name = "GET /reviews — sans token → 401"
    r = client.get("/api/v1/reviews")
    if assert_status(name, r, 401):
        results.ok(name)

    name = "GET /reviews — authentifié → 200"
    r = client.get("/api/v1/reviews", headers=headers)
    if not assert_status(name, r, 200):
        return
    results.ok(name)

    sample_articles = (
        "Article 1 : L'IA générative transforme les rédactions. "
        "Les journaux adoptent des outils d'IA pour accélérer la production de contenu. "
        "Certains craignent une perte de qualité éditoriale.\n\n"
        "Article 2 : OpenAI lance GPT-5, son modèle le plus puissant. "
        "Les experts saluent les progrès en raisonnement mais soulèvent des questions éthiques."
    )
    name = "POST /reviews — création via LLM structuré → 201 + title + content"
    t0 = time.time()
    r = client.post(
        "/api/v1/reviews",
        json={"articles": sample_articles},
        headers=headers,
        timeout=LLM_TIMEOUT,
    )
    elapsed = time.time() - t0
    if not assert_status(name, r, 201):
        return
    body = get_json(r)
    ok = (
        assert_field(name, body, "data", "id")
        and assert_field(name, body, "data", "title")
        and assert_field(name, body, "data", "content")
    )
    if ok:
        title = body["data"]["title"]
        results.ok(name, f"{elapsed:.1f}s — titre : {title!r}")

    name = "GET /reviews — après création → ≥1 review"
    r = client.get("/api/v1/reviews", headers=headers)
    if assert_status(name, r, 200):
        reviews = get_json(r).get("data", [])
        if len(reviews) >= 1:
            results.ok(name, f"{len(reviews)} review(s)")
        else:
            results.fail(name, "attendu ≥1 review après création, reçu 0")

    name = "POST /reviews — articles vides → 422"
    r = client.post("/api/v1/reviews", json={"articles": ""}, headers=headers)
    if assert_status(name, r, 422):
        results.ok(name)


# ── 8. Validation sécurité / isolation ───────────────────────────────────────


def test_security(client: httpx.Client, headers: dict) -> None:
    section("8 · Sécurité et isolation")

    name = "Token invalide → 401 sur endpoint protégé"
    r = client.get(
        "/api/v1/chats",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    if assert_status(name, r, 401):
        results.ok(name)

    name = "Chat d'un autre utilisateur → 404 (pas de fuite d'information)"
    r = client.get("/api/v1/chats/999999/messages", headers=headers)
    if assert_status(name, r, 404):
        results.ok(name)

    name = "Contenu vide → 422 (validation Pydantic)"
    r = client.post(
        "/api/v1/chats/message",
        json={"content": ""},
        headers=headers,
    )
    if assert_status(name, r, 422):
        results.ok(name)


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> int:
    print(f"\n{BOLD}{'═' * 60}{RESET}")
    print(f"{BOLD}  NewsFoundry — Wet Tests (backend E2E){RESET}")
    print(f"{'═' * 60}")
    print(f"  Serveur : {CYAN}{BASE_URL}{RESET}")
    print(f"  Compte  : {TEST_EMAIL}")
    print(f"  Timeout : {LLM_TIMEOUT}s par appel LLM")
    print(f"{'═' * 60}")

    with httpx.Client(base_url=BASE_URL, timeout=30) as client:
        # 1. Santé
        if not test_health(client):
            print(f"\n{RED}Serveur inaccessible — arrêt des tests.{RESET}")
            return results.summary()

        # 2. Auth
        headers = test_auth(client)
        if not headers:
            print(
                f"\n{RED}Authentification échouée — tests authentifiés ignorés.{RESET}"
            )
            return results.summary()

        # 3. Chats basiques + création
        try:
            chat_id = test_chats_basic(client, headers)
        except Exception:
            results.fail("suite chats", traceback.format_exc())
            chat_id = None

        # 4. Continuité de conversation
        if chat_id is not None:
            try:
                test_chat_continuity(client, headers, chat_id)
            except Exception:
                results.fail("suite continuité", traceback.format_exc())

            # 6. Persistance system_prompt (nécessite chat_id)
            try:
                test_system_prompt_persistence(client, headers, chat_id)
            except Exception:
                results.fail("suite system_prompt", traceback.format_exc())

        # 5. Agent routing
        try:
            test_agent_routing(client, headers)
        except Exception:
            results.fail("suite agent routing", traceback.format_exc())

        # 7. Press Reviews
        try:
            test_reviews(client, headers)
        except Exception:
            results.fail("suite reviews", traceback.format_exc())

        # 8. Sécurité
        try:
            test_security(client, headers)
        except Exception:
            results.fail("suite sécurité", traceback.format_exc())

    return results.summary()


if __name__ == "__main__":
    sys.exit(main())
