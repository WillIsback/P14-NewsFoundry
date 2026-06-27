---
title: Déploiement
description: Déploiement Railway, Docker, Tailscale
---

# Déploiement

## Architecture de déploiement

```
[GitHub] push sur main
    │
    ├── GitHub Actions
    │   ├── Tests backend (pytest)
    │   ├── Tests frontend (Vitest)
    │   ├── Tests E2E (Playwright)
    │   └── Wet test (backend production + vrai LLM)
    │
    ├── Vercel (frontend)
    │   └── news-foundry-lime.vercel.app
    │
    └── Railway (backend + base de données)
        └── p14-newsfoundry-production.up.railway.app
```

## Plateformes

### Frontend : Vercel

- **URL :** [https://news-foundry-lime.vercel.app/](https://news-foundry-lime.vercel.app/)
- **Framework :** Next.js 16 (App Router)
- **Déploiement :** automatique depuis GitHub sur la branche `main`
- **Variables d'environnement :**
  - `SESSION_SECRET` : clé de chiffrement des cookies
  - `BACKEND_URL` : URL du backend Railway
  - `SENTRY_DSN`, `SENTRY_ORG`, `SENTRY_PROJECT` : monitoring

### Backend : Railway

- **URL :** [https://p14-newsfoundry-production.up.railway.app](https://p14-newsfoundry-production.up.railway.app)
- **Application :** conteneur Dockerisé (multi-stage build)
- **Déploiement :** automatique depuis GitHub sur la branche `main`
- **Root Directory :** `backend/`

#### Dockerfile

Le build multi-stage (`backend/Dockerfile`) comprend :
1. **Stage builder** : installe les dépendances Python avec `uv`, pré-télécharge le modèle ONNX FastEmbed
2. **Stage runtime** : image `python:3.13-slim-bookworm`, utilisateur non-root (`uid 1001`)

```dockerfile
# Points clés du Dockerfile
- Utilisateur non-root pour la sécurité
- Cache ONNX pré-téléchargé (évite le téléchargement au démarrage)
- HEALTHCHECK sur le endpoint racine
- Variables d'environnement : PATH, PYTHONUNBUFFERED, FASTEMBED_CACHE_PATH
```

### Base de données : Railway PostgreSQL

- Base de données PostgreSQL managée, créée dans le même projet Railway que le backend
- Migrations gérées par Alembic via le `release command` : `uv run src/bootstrap.py`
- En développement : SQLite in-memory

## CI/CD

### Déclencheurs

- **push** sur `main` : tous les tests + déploiement
- **pull_request** vers `main` : tests uniquement, pas de déploiement

### Workflows GitHub Actions

| Workflow | Rôle |
|----------|------|
| `backend-tests.yml` | pytest + wet test post-merge (sur runner auto-hébergé avec Tailscale) |
| `frontend-tests.yml` | Vitest avec rapport de couverture |
| `playwright-e2e.yml` | Tests E2E Playwright avec build Next.js |
| `ai-code-review.yml` | Revue de code IA (vLLM auto-hébergé) |
| `prod-smoke-test.yml` | Health check post-déploiement (manuel ou webhook Railway) |
| `dependabot-auto-merge.yml` | Merge automatique des dépendances |

### Pipeline de déploiement

1. **Push sur `main`** déclenche les workflows
2. **Tests unitaires** (pytest + Vitest) : bloquants
3. **Tests E2E** (Playwright) : avec serveur mock Express
4. **Déploiements parallèles** :
   - Vercel déploie le frontend automatiquement
   - Railway build l'image Docker et exécute les migrations
5. **Wet test** (backend uniquement) : exécuté après le déploiement Railway, valide la chaîne complète avec un vrai LLM
6. **Smoke test** : health check manuel ou post-déploiement Railway (3 tentatives avec intervalle de 10s)

### Runners

- **Tests standard :** `ubuntu-latest` (GitHub-hosted)
- **Wet test :** `self-hosted` (nécessite accès Tailscale au LLM)

### Secrets requis

| Secret | Utilisation |
|--------|-------------|
| `SESSION_SECRET` | Chiffrement des cookies frontend |
| `ADMIN_EMAIL` | Compte admin bootstrap + wet test |
| `ADMIN_PASSWORD` | Mot de passe admin |
| `LLM_BASE_URL` | URL du endpoint vLLM |
| `LLM_API_KEY` | Clé API LLM |
| `LLM_MODEL` | Nom du modèle LLM |
| `E2E_SESSION_SECRET` | Secret pour les tests E2E |

### Connectivité LLM

En production, le backend Railway accède au LLM (vLLM) via un proxy Tailscale. Le runner GitHub Actions auto-hébergé a également accès à Tailscale pour exécuter les wet tests.

```
[Backend Railway] → LLM_PROXY_URL (proxy HTTP Tailscale) → [Serveur vLLM]
[Runner self-hosted] → LLM_BASE_URL direct → [Serveur vLLM]
```
