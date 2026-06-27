---
title: Tests
description: Stratégie de tests — Vitest, Testing Library, Playwright
---

# Tests

## Stratégie de test

L'application utilise trois niveaux de tests :

```
Tests unitaires (pytest + Vitest)
    → Tests d'intégration (backend tests avec TestClient)
        → Tests E2E (Playwright)
            → Tests d'intégration humides (wet tests sur Railway)
```

## Backend (pytest)

### Configuration

- **Framework :** pytest 9+ avec `pytest-asyncio` (mode strict)
- **Base de données :** SQLite in-memory (remplace PostgreSQL)
- **Client HTTP :** FastAPI TestClient

### Fixtures principales (`conftest.py`)

| Fixture | Description |
|---------|-------------|
| `engine` | Moteur SQLite in-memory avec `check_same_thread=False` |
| `client` | TestClient FastAPI avec DB overridée et lifespan désactivée |
| `client_two_users` | Deux utilisateurs seedés + un chat avec messages |

### Fichiers de test

| Fichier | Couverture |
|---------|------------|
| `test_chats_authorization.py` | Isolation des données : accès autorisé/interdit aux discussions d'autrui |
| `test_authentication.py` | Connexion, création de token, endpoints protégés |
| `test_news_endpoints.py` | Endpoints de contexte d'actualités |
| `test_news_search.py` | Service de recherche WorldNewsAPI |
| `test_news_service.py` | Orchestration de la pipeline d'actualités |
| `test_labeler.py` | Étiquetage LLM des clusters |
| `test_reducer.py` | Logique de réduction des clusters |
| `test_llm_client.py` | Création du client LLM |
| `test_prompt_builder.py` | Construction des prompts |
| `test_press_review_agent.py` | Agent de revue de presse (sortie structurée) |
| `test_press_review_crud.py` | Opérations CRUD des revues de presse |
| `test_press_review_endpoints.py` | Endpoints de revue de presse |
| `test_rag_indexer.py` | Index et recherche RAG |
| `test_topnewscontext_model.py` | Modèle TopNewsContext |
| `test_agent_tools.py` | Outils des agents |
| `test_exception_handler_responses.py` | Réponses des handlers d'erreurs HTTP |
| `test_worldnews.py` | Client WorldNewsAPI (mock inclus) |

### Test d'autorisation critique

`test_chats_authorization.py` contient deux tests essentiels :

1. **test_owner_can_read_their_chat_messages** : vérifie qu'un utilisateur peut accéder à ses propres messages (cas nominal)
2. **test_other_user_cannot_access_or_modify_owner_chat** : vérifie qu'un utilisateur ne peut ni lire (GET) ni modifier (POST) les discussions d'un autre utilisateur — les deux appels retournent 404

### Wet test (test d'intégration humide)

`wet_test_endpoints.py` est un test d'intégration (712 lignes) qui s'exécute contre le backend Railway de production :
- Vérifie la santé, l'authentification, les discussions, l'agent conversationnel, et les revues de presse
- Consomme de vrais tokens LLM
- Nécessite un runner GitHub Actions auto-hébergé avec accès Tailscale

## Frontend (Vitest)

### Configuration

- **Framework :** Vitest avec jsdom
- **Seuil de couverture :** 80% (branches, functions, lines, statements)
- **Provider :** V8

### Fichiers de test

| Fichier | Couverture |
|---------|------------|
| `components/__tests__/ChatForm.test.tsx` | Rendu du formulaire, états des boutons |
| `components/__tests__/ChatWindow.test.tsx` | Rendu du chat, scroll, messages |
| `components/__tests__/AssistantCard.test.tsx` | Affichage de l'assistant, état par défaut |
| `components/__tests__/HomeChatWrapper.test.tsx` | Wrapper de chat sur la page d'accueil |
| `components/ui/__tests__/Message.test.tsx` | Rendu des messages utilisateur/AI, Markdown, timestamps, snapshot |
| `components/ui/__tests__/AssistantPendingContent.test.tsx` | Indicateur de chargement assistant |
| `components/ui/__tests__/PendingSpinner.test.tsx` | Spinner de chargement |

## End-to-End (Playwright)

### Configuration

- **Navigateur :** Chromium (headless)
- **Timeout :** 30s
- **Retries :** 2 sur CI

### Architecture des tests E2E

Les tests Playwright utilisent un **serveur mock Express** (`e2e/mocks/api-server.ts`, port 3001) qui simule le backend. Un setup global (`global-setup.ts`) génère des cookies JWT pour 12 scénarios d'authentification différents.

### Fichiers de test

| Fichier | Couverture |
|---------|------------|
| `auth.spec.ts` | Connexion, création de session |
| `chat.spec.ts` | Nouvelle discussion, continuation, messages |
| `review.spec.ts` | Génération de revue de presse |
| `isolation.spec.ts` | Isolation des données utilisateur A/B |
| `errors.spec.ts` | Gestion des erreurs 500, timeout, rate limit |
| `unhappy-path.spec.ts` | Erreur 404, fallback UI |

## Intégration continue (CI)

### Workflows GitHub Actions

| Workflow | Déclencheur | Description |
|----------|-------------|-------------|
| `frontend-tests.yml` | PR/push main (frontend/**) | Vitest + couverture |
| `backend-tests.yml` | PR/push main (backend/**) | pytest + wet test post-merge |
| `playwright-e2e.yml` | PR/push main (frontend/**) | Playwright + rapport |
| `ai-code-review.yml` | PR (backend/** ou frontend/**) | Revue de code IA |
| `prod-smoke-test.yml` | Manuel + webhook Railway | Health check production |
| `dependabot-auto-merge.yml` | PR Dependabot | Merge automatique |
| `pr-autolink-issue.yml` | Création PR | Lien PR ↔ issue |
| `pr-issue-check.yml` | Création PR | Validation référence issue |

### Exécution en CI

```bash
# Backend
uv run pytest tests/ -v --tb=short

# Frontend
pnpm test:coverage
pnpm e2e
```
