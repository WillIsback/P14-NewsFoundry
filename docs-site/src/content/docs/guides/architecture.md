---
title: Architecture
description: Architecture technique de NewsFoundry
---

# Architecture du projet

## Structure des dossiers

```
NewsFoundry/
├── backend/                          # API Python / FastAPI
│   ├── alembic/                      # Migrations de base de données (6 révisions)
│   ├── alembic.ini
│   ├── Dockerfile                    # Build multi-stage pour le déploiement
│   ├── docker-entrypoint.sh
│   ├── pyproject.toml
│   ├── src/
│   │   ├── main.py                   # Point d'entrée FastAPI, factory create_app()
│   │   ├── api/
│   │   │   ├── router.py             # Enregistrement de tous les routers
│   │   │   ├── models.py             # Modèles Pydantic de l'API (requêtes/réponses)
│   │   │   ├── authentication_endpoints.py
│   │   │   ├── chat_endpoints.py
│   │   │   ├── review_endpoints.py
│   │   │   ├── news_endpoints.py
│   │   │   └── health_endpoints.py
│   │   ├── core/
│   │   │   ├── config.py             # Configuration centralisée (55+ variables d'env)
│   │   │   ├── auth.py               # JWT creation et dépendance verify_user
│   │   │   ├── security.py           # Hachage bcrypt, tokens
│   │   │   ├── middleware.py         # Rate limiting, auth, en-têtes de sécurité
│   │   │   ├── prompts.py            # Définitions des system prompts LLM
│   │   │   ├── llm_client.py         # Factory AsyncOpenAI singleton
│   │   │   ├── llm_provider.py       # call_llm, call_llm_structured, compaction
│   │   │   ├── agent/
│   │   │   │   ├── search_agent.py   # Agent de chat principal avec outils news
│   │   │   │   ├── press_review_agent.py  # Agent de génération de revue de presse
│   │   │   │   ├── tools.py          # Outils get_top_news et search_news
│   │   │   │   └── context.py        # Dataclass ChatRunContext
│   │   │   ├── news/
│   │   │   │   ├── service.py        # Orchestrateur fetch_and_build_context
│   │   │   │   ├── search.py         # Recherche WorldNewsAPI
│   │   │   │   ├── reducer.py        # Réduction et tri des clusters
│   │   │   │   └── labeler.py        # Étiquetage LLM des clusters
│   │   │   ├── rag/
│   │   │   │   └── indexer.py        # Index vectoriel LlamaIndex + FastEmbed
│   │   │   └── worldnewsapi/
│   │   │       ├── worldnews.py      # Client auto-généré NewsApi + Mock
│   │   │       └── mock_data.py      # Réponses mockées pour le développement
│   │   ├── database/
│   │   │   ├── database.py           # Initialisation et sessions SQLModel
│   │   │   ├── models.py             # Modèles SQLModel (User, Chat, Message, PressReview, TopNewsContext)
│   │   │   └── crud.py               # Opérations CRUD synchrones et asynchrones
│   │   └── utils/
│   │       └── utils.py              # Utilitaires (sanitization, LLMMessage)
│   └── tests/                        # 17 fichiers de test + 1 test d'intégration
│       ├── conftest.py
│       ├── test_chats_authorization.py
│       ├── test_authentication.py
│       ├── (... 15 autres fichiers)
│       └── wet_test_endpoints.py     # Test E2E contre le backend de production
├── frontend/                         # Application Next.js
│   ├── src/
│   │   ├── app/
│   │   │   ├── (public)/             # Pages publiques (login)
│   │   │   ├── (private)/            # Pages authentifiées (home, chat)
│   │   │   ├── layout.tsx
│   │   │   └── globals.css
│   │   ├── actions/
│   │   │   ├── auth.action.ts        # Server Actions : loginUser, logout
│   │   │   ├── chat.action.ts        # Server Actions : chats, messages
│   │   │   └── review.action.ts      # Server Actions : reviews
│   │   ├── service/
│   │   │   ├── auth.dal.ts           # DAL : postLogin
│   │   │   ├── chat.dal.ts           # DAL : getChats, getMessages, postMessage
│   │   │   └── review.dal.ts         # DAL : getReviews, postCreateReview
│   │   ├── lib/
│   │   │   ├── fetch.lib.ts          # Client HTTP typé avec timeout, Zod, auto-redirect
│   │   │   ├── session.ts            # Gestion des sessions JWT (cookies HTTP-only)
│   │   │   ├── type.lib.ts           # Types partagés (ServiceResult, SessionTokenPayload)
│   │   │   ├── auth-helpers.ts       # Schémas de validation login
│   │   │   └── utils.ts              # Utilitaire Tailwind
│   │   ├── components/
│   │   │   └── ui/                   # Composants d'interface
│   │   └── models/gen/               # Schémas Zod auto-générés (Kubb)
│   ├── e2e/                          # Tests Playwright
│   │   ├── tests/                    # 6 fichiers de test
│   │   ├── mocks/api-server.ts       # Serveur Express mocké
│   │   ├── fixtures/                 # Données de test et sessions pré-computées
│   │   └── global-setup.ts           # Génération des cookies JWT
│   └── playwright.config.ts
├── docs/                             # Documentation du projet
├── .github/
│   └── workflows/                    # 9 workflows CI/CD
└── README.md
```

## Flux de données

```
Utilisateur (navigateur)
    │
    ▼
Next.js Server Components
    │ (Server Actions)
    ▼
Service Layer (DAL) ─── fetch.lib.ts (timeout + Zod + auto-redirect 401)
    │
    ▼
Backend API (FastAPI /api/v1/*)
    │
    ├── Authentification → JWT → PostgreSQL (users)
    ├── Chat → OpenAI Agents SDK → LLM (vLLM)
    │         → WorldNewsAPI → news context
    │         → LlamaIndex/FastEmbed → RAG
    │         → PostgreSQL (chats, messages, topnewscontext)
    └── Revue de presse → LLM structuré → PostgreSQL (pressreviews)
```

## Flux de déploiement

```
Développeur → push sur main
    │
    ├── GitHub Actions (tests unitaires + lint)
    │   ├── frontend-tests.yml (Vitest + couverture)
    │   ├── backend-tests.yml (pytest)
    │   ├── playwright-e2e.yml (Playwright)
    │   └── backend-tests.yml → wet-test (E2E production)
    │
    ├── Vercel (frontend) → déploiement automatique
    │
    └── Railway (backend) → Docker build + release command
        ├── PostgreSQL (base de données)
        └── LLM via proxy Tailscale
```
