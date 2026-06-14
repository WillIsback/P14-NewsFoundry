# Choix techniques

## Stack générale

### Next.js (Frontend)

**Choix :** Next.js 16 avec App Router.

Next.js est le choix naturel pour une application fullstack moderne : il offre le Server-Side Rendering (SSR) pour le SEO et les performances perçues, les Server Actions pour les mutations sans API Route dédiée, et un écosystème riche. L'App Router permet un routage basé sur les dossiers avec des layouts imbriqués, ce qui facilite la séparation entre pages publiques et privées via des `Route Groups`.

### Python + FastAPI (Backend)

**Choix :** Python 3.13, FastAPI, SQLModel.

Python est incontournable pour l'écosystème IA/LLM (OpenAI SDK, LlamaIndex, etc.). FastAPI offre des performances élevées (asynchrone natif), une validation automatique via Pydantic, et une documentation OpenAPI générée automatiquement. SQLModel combine SQLAlchemy et Pydantic pour une expérience unifiée entre l'ORM et les schémas de validation.

### Base de données PostgreSQL

**Choix :** PostgreSQL sur Railway.

PostgreSQL est une base de données relationnelle robuste, adaptée aux données structurées de l'application (utilisateurs, discussions, messages, revues de presse). Railway fournit une instance PostgreSQL managée avec sauvegardes automatiques.

### ORM : SQLModel

**Choix :** SQLModel (SQLAlchemy + Pydantic).

SQLModel permet de définir les modèles de base de données et les schémas Pydantic en une seule classe, éliminant la duplication. Il s'intègre nativement avec FastAPI pour la validation des requêtes et réponses.

### Authentification : JWT

**Choix :** JSON Web Tokens (JWT) avec `python-jose` (backend) et `jose` (frontend).

Les JWT permettent une authentification sans état (stateless), idéale pour une API REST. Le backend génère un token signé en HMAC-SHA256. Le frontend stocke ce token dans un cookie HTTP-only chiffré côté serveur (Next.js Server Action), offrant une protection contre les attaques XSS.

## IA et LLM

### OpenAI Agents SDK

**Choix :** `openai-agents` pour l'orchestration des agents conversationnels.

L'OpenAI Agents SDK offre un framework structuré pour créer des agents avec des outils, du contexte, et des sorties typées. Il est utilisé pour :
- L'agent de chat (`search_agent.py`) avec les outils `get_top_news` et `search_news`
- L'agent de revue de presse (`press_review_agent.py`) avec sortie structurée `PressReviewOutput`

### LlamaIndex + FastEmbed (RAG)

**Choix :** LlamaIndex Core + FastEmbed (ONNX, local).

Le Retrieval-Augmented Generation (RAG) permet d'enrichir les réponses du LLM avec les articles de presse déjà chargés. FastEmbed exécute le modèle `paraphrase-multilingual-MiniLM-L12-v2` en local via ONNX, sans dépendre d'une API externe d'embeddings.

### WorldNewsAPI

**Choix :** WorldNewsAPI pour les sources d'actualités.

L'API WorldNewsAPI fournit un accès à des milliers de sources d'actualités internationales. Le SDK auto-généré est encapsulé avec un mode mock (réponses fixes en développement) pour éviter les limites de taux et les coûts pendant le développement.

### Fournisseur LLM : vLLM

**Choix :** vLLM (self-hosted) accessible via Tailscale.

L'infrastructure LLM est auto-hébergée via vLLM sur un serveur dédié, accessible depuis Railway via un proxy Tailscale. Cela permet un contrôle complet sur le modèle utilisé, les coûts, et la latence. En développement, le backend se connecte directement à l'instance vLLM locale.

## Frontend

### Tailwind CSS + shadcn/ui

**Choix :** Tailwind CSS 4 + shadcn/ui (Radix UI primitives).

Tailwind CSS permet un développement rapide avec des classes utilitaires, sans écrire de CSS personnalisé. shadcn/ui fournit des composants accessibles et personnalisables basés sur Radix UI, avec une intégration transparente dans Tailwind.

### React 19 Server Actions

**Choix :** Server Actions avec `useActionState` pour la gestion d'état.

Les Server Actions de Next.js (React 19) permettent d'effectuer des mutations côté serveur sans exposer d'API REST supplémentaire. Chaque action suit le pattern : `Server Action → DAL (Data Access Layer) → fetch.lib.ts → Backend`. L'état des formulaires est géré avec `useActionState()`.

### Zod (v4)

**Choix :** Zod pour la validation des schémas côté frontend.

Zod permet de valider les réponses API à l'exécution, garantissant que le frontend reçoit bien les données attendues. Les schémas sont soit auto-générés via Kubb (OpenAPI codegen) soit écrits manuellement.

### pnpm

**Choix :** pnpm comme gestionnaire de paquets.

pnpm est plus rapide et plus économe en espace disque que npm ou yarn grâce à son système de liens symboliques et son cache global.

## Déploiement

### Vercel (Frontend)

**Choix :** Vercel pour le déploiement du frontend Next.js.

Vercel est la plateforme d'hébergement officielle de Next.js, offrant un déploiement optimisé, des aperçus de PR, et une intégration Git native.

### Railway (Backend + Base de données)

**Choix :** Railway pour le backend et la base de données.

Railway simplifie le déploiement d'applications Dockerisées avec des déploiements automatiques, une base de données PostgreSQL managée, et des domaines personnalisés.

### CI/CD : GitHub Actions

**Choix :** GitHub Actions pour l'intégration continue.

8 workflows automatisent les tests, l'analyse de code, et les déploiements. Les workflows sont déclenchés sur `push` et `pull_request` sur `main`.

## Dépendances principales

### Backend (Python)
| Dépendance | Rôle |
|------------|------|
| `fastapi >= 0.136.1` | Framework API |
| `sqlmodel >= 0.0.38` | ORM unifié |
| `openai >= 2.36.0` | Client LLM |
| `openai-agents >= 0.17.4` | Agents IA |
| `llama-index-core >= 0.12` | RAG |
| `llama-index-embeddings-fastembed >= 0.2` | Embeddings locaux |
| `worldnewsapi >= 2.2.0` | Actualités |
| `sentry-sdk >= 2.60.0` | Surveillance d'erreurs |
| `python-jose[cryptography] >= 3.3.0` | JWT |
| `bcrypt >= 5.0.0` | Hachage mots de passe |
| `httpx[socks] >= 0.28.1` | Proxy Tailscale |

### Frontend (Node.js)
| Dépendance | Rôle |
|------------|------|
| `next` 16.2.4 | Framework React |
| `react`, `react-dom` 19.2.4 | UI |
| `tailwindcss` 4 | Styles |
| `radix-ui` | Composants accessibles |
| `zod` 4.4.3 | Validation |
| `jose` | JWT |
| `sonner` | Notifications |
| `react-markdown` | Rendu Markdown |
| `lucide-react` | Icônes |
| `@sentry/nextjs` | Monitoring |
| `@playwright/test` | Tests E2E |
| `vitest` | Tests unitaires |
