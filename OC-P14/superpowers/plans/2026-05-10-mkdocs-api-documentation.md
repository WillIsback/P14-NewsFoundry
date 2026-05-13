# MkDocs API Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mettre en place un site MkDocs dans `backend/docs/` avec des guides narratifs et une page de référence API intégrant Swagger UI via CDN, tout en déplaçant les routes Swagger natives de FastAPI sur `/api/docs`.

**Architecture:** MkDocs autonome (thème readthedocs) dans `backend/docs/`, buildable et déployable indépendamment du backend. FastAPI expose `/openapi.json` en permanence et déplace son Swagger UI sur `/api/docs` (désactivé en production). La page `api-reference.md` charge Swagger UI depuis CDN en pointant vers `/openapi.json`.

**Tech Stack:** Python 3.13, FastAPI, MkDocs >= 1.6, uv (gestionnaire de paquets), pytest + TestClient (tests)

---

## Fichiers touchés

| Action | Chemin |
|--------|--------|
| Modifier | `backend/src/main.py` |
| Modifier | `backend/pyproject.toml` |
| Créer | `backend/docs/mkdocs.yml` |
| Créer | `backend/docs/docs/index.md` |
| Créer | `backend/docs/docs/getting-started.md` |
| Créer | `backend/docs/docs/authentication.md` |
| Créer | `backend/docs/docs/api-reference.md` |
| Créer | `backend/docs/docs/changelog.md` |
| Créer | `backend/docs/.gitignore` |
| Modifier (test) | `backend/tests/test_authentication.py` |

---

### Task 1 : Déplacer les routes Swagger de FastAPI

**Contexte :** FastAPI expose par défaut Swagger UI sur `/docs` et ReDoc sur `/redoc`. On veut les déplacer sur `/api/docs` et `/api/redoc`, et les désactiver complètement en production (`APP_ENV=production`) tout en gardant `/openapi.json` actif.

**Files:**
- Modify: `backend/src/main.py`
- Test: `backend/tests/test_authentication.py`

- [ ] **Step 1 : Écrire les tests qui vont échouer**

Ajouter en bas de `backend/tests/test_authentication.py` :

```python
def test_swagger_ui_is_on_api_docs(client: TestClient) -> None:
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()


def test_old_docs_route_is_gone(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 404


def test_openapi_json_always_accessible(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    payload = response.json()
    assert "openapi" in payload
    assert payload["info"]["title"] == "NewsFoundry backend API"
```

- [ ] **Step 2 : Lancer les tests pour vérifier qu'ils échouent**

```bash
cd backend
uv run pytest tests/test_authentication.py::test_swagger_ui_is_on_api_docs tests/test_authentication.py::test_old_docs_route_is_gone tests/test_authentication.py::test_openapi_json_always_accessible -v
```

Résultat attendu : `FAILED` — `/api/docs` retourne 404, `/docs` retourne 200.

- [ ] **Step 3 : Modifier `backend/src/main.py`**

Remplacer le bloc de création de l'app FastAPI (lignes 37-42 actuellement) :

```python
app = FastAPI(
    lifespan=lifespan,
    title="NewsFoundry backend API",
    description="Backend API for NewsFoundry application",
    version="1.0.0",
    docs_url=None if APP_ENV == "production" else "/api/docs",
    redoc_url=None if APP_ENV == "production" else "/api/redoc",
)
```

L'import `APP_ENV` est déjà présent ligne 18 : `from core.config import CORS_ORIGINS, DEBUG_MODE, APP_ENV`.

- [ ] **Step 4 : Relancer les tests pour vérifier qu'ils passent**

```bash
cd backend
uv run pytest tests/test_authentication.py -v
```

Résultat attendu : tous les tests `PASSED`.

- [ ] **Step 5 : Commiter**

```bash
cd backend
git add src/main.py tests/test_authentication.py
git commit -m "feat(api): move swagger UI to /api/docs, disable in production"
```

---

### Task 2 : Ajouter MkDocs comme dépendance de dev

**Contexte :** MkDocs est un outil de documentation uniquement, pas une dépendance runtime. On l'ajoute dans un groupe `dev` de `pyproject.toml` via `uv`.

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1 : Ajouter mkdocs via uv**

```bash
cd backend
uv add --group dev mkdocs
```

Résultat attendu : `pyproject.toml` et `uv.lock` mis à jour, `mkdocs` installé dans `.venv`.

- [ ] **Step 2 : Vérifier l'installation**

```bash
cd backend
uv run mkdocs --version
```

Résultat attendu : `mkdocs, version 1.6.x from ...`

- [ ] **Step 3 : Commiter**

```bash
cd backend
git add pyproject.toml uv.lock
git commit -m "chore(deps): add mkdocs as dev dependency"
```

---

### Task 3 : Créer la structure MkDocs et la configuration

**Contexte :** MkDocs attend un fichier `mkdocs.yml` à la racine du projet MkDocs, et les sources Markdown dans un sous-dossier `docs/`. On place tout dans `backend/docs/` pour que MkDocs reste autonome. Le dossier `site/` (généré) est gitignored.

**Files:**
- Créer: `backend/docs/mkdocs.yml`
- Créer: `backend/docs/.gitignore`
- Créer: `backend/docs/docs/` (dossier vide pour l'instant)

- [ ] **Step 1 : Créer les dossiers**

```bash
mkdir -p backend/docs/docs
```

- [ ] **Step 2 : Créer `backend/docs/.gitignore`**

```
site/
```

- [ ] **Step 3 : Créer `backend/docs/mkdocs.yml`**

```yaml
site_name: NewsFoundry API
site_description: Documentation de l'API backend NewsFoundry
site_author: NewsFoundry Team
docs_dir: docs
site_dir: site

theme:
  name: readthedocs

nav:
  - Accueil: index.md
  - Démarrage rapide: getting-started.md
  - Guides:
    - Authentification: authentication.md
  - Référence API: api-reference.md
  - Changelog: changelog.md
```

- [ ] **Step 4 : Vérifier que MkDocs reconnaît la config**

```bash
cd backend/docs
uv run --directory .. mkdocs build --strict 2>&1 | head -5
```

Résultat attendu : erreur sur les fichiers `.md` manquants (normal à ce stade) — mais pas d'erreur de config YAML.

- [ ] **Step 5 : Commiter**

```bash
cd backend
git add docs/mkdocs.yml docs/.gitignore
git commit -m "chore(docs): initialize MkDocs project structure"
```

---

### Task 4 : Écrire `index.md` et `getting-started.md`

**Contexte :** Pages d'entrée du site. `index.md` présente le projet, `getting-started.md` guide l'installation locale.

**Files:**
- Créer: `backend/docs/docs/index.md`
- Créer: `backend/docs/docs/getting-started.md`

- [ ] **Step 1 : Créer `backend/docs/docs/index.md`**

```markdown
# NewsFoundry API

Bienvenue dans la documentation de l'API backend **NewsFoundry**.

NewsFoundry est une plateforme de gestion de contenu journalistique. Cette API expose les ressources et actions disponibles pour les clients (frontend web, applications mobiles, intégrations tierces).

## Liens rapides

| Ressource | Lien |
|-----------|------|
| Démarrage rapide | [getting-started.md](getting-started.md) |
| Authentification | [authentication.md](authentication.md) |
| Référence API interactive | [api-reference.md](api-reference.md) |
| Changelog | [changelog.md](changelog.md) |

## Versioning

L'API suit le préfixe `/api/v1`. Les changements breaking sont introduits sur une nouvelle version de préfixe (`/api/v2`).

## Support

Pour toute question ou bug, ouvrez une issue sur le dépôt GitHub du projet.
```

- [ ] **Step 2 : Créer `backend/docs/docs/getting-started.md`**

```markdown
# Démarrage rapide

## Prérequis

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (gestionnaire de paquets Python)
- Docker (pour PostgreSQL local)
- Git

## Installation

### 1. Cloner le dépôt

```bash
git clone <repo-url>
cd NewsFoundry/backend
```

### 2. Copier la configuration d'environnement

```bash
cp .env.example .env
```

Ajuster les variables dans `.env` :

```env
APP_ENV=development
DATABASE_URL=postgresql://user:password@localhost:5432/newsfoundry
SECRET_KEY=your_dev_secret_key_change_in_prod
SEED_DEFAULT_USER=true
DEFAULT_USER_EMAIL=test@test.com
DEFAULT_USER_PASSWORD=test
```

### 3. Installer les dépendances

```bash
uv sync
```

### 4. Démarrer PostgreSQL

```bash
docker run \
  --name newsfoundry_db \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=newsfoundry \
  -p 5432:5432 \
  -d postgres:17
```

### 5. Lancer le backend

```bash
uv run --env-file .env src/main.py
```

Le backend applique automatiquement les migrations Alembic au démarrage en mode `development`.

## Vérification

```bash
curl http://localhost:8000/
```

Réponse attendue :

```json
{
  "success": true,
  "status": 200,
  "message": "API reachable",
  "data": { "message": "👋" },
  "error": null
}
```

## Swagger UI (développement uniquement)

En mode développement, le Swagger UI interactif est disponible sur :

```
http://localhost:8000/api/docs
```

> **Note :** Le Swagger UI natif est désactivé en production. Utilisez la [page de référence API](api-reference.md) de ce site pour explorer l'API.

## Lancer les tests

```bash
uv run pytest tests/ -v
```
```

- [ ] **Step 3 : Vérifier que MkDocs parse les pages sans erreur**

```bash
cd backend/docs
uv run --directory .. mkdocs build --strict 2>&1 | grep -E "ERROR|WARNING|error" | head -10
```

Résultat attendu : warnings sur les pages manquantes (`authentication.md`, etc.) — les pages créées ne doivent pas produire d'erreur.

- [ ] **Step 4 : Commiter**

```bash
cd backend
git add docs/docs/index.md docs/docs/getting-started.md
git commit -m "docs: add index and getting-started pages"
```

---

### Task 5 : Écrire `authentication.md`

**Contexte :** Guide narratif expliquant le flux d'authentification JWT de l'API — login, token Bearer, routes protégées — avec exemples `curl`.

**Files:**
- Créer: `backend/docs/docs/authentication.md`

- [ ] **Step 1 : Créer `backend/docs/docs/authentication.md`**

```markdown
# Authentification

L'API NewsFoundry utilise **JWT (JSON Web Tokens)** avec le schéma Bearer pour authentifier les requêtes sur les routes protégées.

## Flux d'authentification

```
Client                          API
  │                              │
  │  POST /api/v1/auth/login     │
  │  { email, password }         │
  │─────────────────────────────>│
  │                              │ Vérifie credentials
  │  { access_token, "bearer" }  │ en base de données
  │<─────────────────────────────│
  │                              │
  │  GET /api/v1/auth/users/me   │
  │  Authorization: Bearer <tok> │
  │─────────────────────────────>│
  │                              │ Vérifie signature JWT
  │  { id, email }               │
  │<─────────────────────────────│
```

## Obtenir un token

**Endpoint :** `POST /api/v1/auth/login`

Le body doit être encodé en `application/x-www-form-urlencoded` (formulaire HTML standard).

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=test@test.com&password=test"
```

Réponse :

```json
{
  "success": true,
  "status": 200,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  },
  "error": null
}
```

Le token expire après **30 minutes** (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).

## Utiliser le token

Pour toutes les requêtes sur des routes protégées, ajouter le header `Authorization` :

```bash
curl http://localhost:8000/api/v1/auth/users/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Réponse :

```json
{
  "success": true,
  "status": 200,
  "message": "Current user retrieved",
  "data": {
    "id": 1,
    "email": "test@test.com"
  },
  "error": null
}
```

## Routes protégées

| Route | Méthode | Description |
|-------|---------|-------------|
| `/api/v1/auth/users/me` | GET | Profil de l'utilisateur courant |
| `/api/v1/auth/protected` | GET | Route de test d'accès protégé |

## Erreurs courantes

### 401 — Credentials invalides

```json
{
  "success": false,
  "status": 401,
  "message": "Identifiant ou mot de passe incorrect",
  "data": null,
  "error": {
    "code": "HTTP_EXCEPTION",
    "message": "Identifiant ou mot de passe incorrect",
    "details": "Identifiant ou mot de passe incorrect"
  }
}
```

### 401 — Token manquant ou invalide

```json
{
  "success": false,
  "status": 401,
  "message": "HTTP error",
  "data": null,
  "error": {
    "code": "HTTP_EXCEPTION",
    "message": "HTTP error",
    "details": "Not authenticated"
  }
}
```

## Format de réponse standard

Toutes les réponses de l'API suivent l'enveloppe `ApiResponse` :

```json
{
  "success": true | false,
  "status": 200 | 401 | 422 | 500,
  "message": "Human-readable message",
  "data": { ... } | null,
  "error": null | { "code": "...", "message": "...", "details": ... }
}
```
```

- [ ] **Step 2 : Commiter**

```bash
cd backend
git add docs/docs/authentication.md
git commit -m "docs: add authentication guide with JWT flow and curl examples"
```

---

### Task 6 : Écrire `api-reference.md` avec Swagger UI CDN

**Contexte :** C'est la page clé. Elle intègre Swagger UI via CDN JavaScript pointant vers `/openapi.json` du backend. En dev, l'URL est `http://localhost:8000/openapi.json`. MkDocs avec le thème readthedocs supporte le HTML brut dans les fichiers Markdown.

**Files:**
- Créer: `backend/docs/docs/api-reference.md`

- [ ] **Step 1 : Créer `backend/docs/docs/api-reference.md`**

```markdown
# Référence API

Cette page affiche la référence interactive complète de l'API NewsFoundry, générée automatiquement depuis la spec OpenAPI du backend.

> **Prérequis :** Le backend doit être lancé localement sur `http://localhost:8000` pour que le Swagger UI ci-dessous soit fonctionnel en développement. En production, pointer l'URL vers le backend Railway déployé.

---

<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">

<div id="swagger-ui" style="margin-top: 1rem;"></div>

<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
  window.onload = function() {
    SwaggerUIBundle({
      url: "http://localhost:8000/openapi.json",
      dom_id: '#swagger-ui',
      deepLinking: true,
      presets: [
        SwaggerUIBundle.presets.apis,
        SwaggerUIBundle.SwaggerUIStandalonePreset
      ],
      layout: "StandaloneLayout"
    });
  };
</script>

---

*Pour pointer vers un backend distant, remplacer l'URL `http://localhost:8000/openapi.json` par l'URL de votre instance déployée.*
```

- [ ] **Step 2 : Vérifier que MkDocs parse la page sans erreur**

```bash
cd backend/docs
uv run --directory .. mkdocs build 2>&1 | grep -E "ERROR|error" | head -5
```

Résultat attendu : aucune erreur (les warnings sur HTML inline sont normaux avec readthedocs).

- [ ] **Step 3 : Commiter**

```bash
cd backend
git add docs/docs/api-reference.md
git commit -m "docs: add api-reference page with Swagger UI CDN embed"
```

---

### Task 7 : Écrire `changelog.md` et vérifier le build complet

**Contexte :** Page de changelog standard. Après création, on lance un build complet + `mkdocs serve` pour vérifier que tout s'affiche correctement.

**Files:**
- Créer: `backend/docs/docs/changelog.md`

- [ ] **Step 1 : Créer `backend/docs/docs/changelog.md`**

```markdown
# Changelog

Tous les changements notables de l'API NewsFoundry sont documentés ici.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

---

## [1.0.0] — 2026-05-10

### Ajouté

- `POST /api/v1/auth/login` — authentification par email/mot de passe, retourne un token JWT Bearer
- `GET /api/v1/auth/protected` — route protégée de test d'accès authentifié
- `GET /api/v1/auth/users/me` — récupération du profil utilisateur courant
- `GET /` — endpoint de santé retournant un message de disponibilité
- Enveloppe de réponse standard `ApiResponse` avec `success`, `status`, `message`, `data`, `error`
- Rate limiting : 100 req/min global, 5 req/min sur le login
- Bootstrap admin idempotent pour la création d'un compte administrateur en production
```

- [ ] **Step 2 : Lancer le build complet**

```bash
cd backend/docs
uv run --directory .. mkdocs build --strict
```

Résultat attendu :
```
INFO    -  Building documentation...
INFO    -  Cleaning site directory
INFO    -  Documentation built in X.XX seconds
```
Pas d'erreur `ERROR` ni de warning `WARNING` bloquant.

- [ ] **Step 3 : Lancer le serveur de dev MkDocs et vérifier visuellement**

```bash
cd backend/docs
uv run --directory .. mkdocs serve --dev-addr 0.0.0.0:8001
```

Ouvrir `http://localhost:8001` dans un navigateur et vérifier :
- [ ] Page d'accueil s'affiche avec les liens rapides
- [ ] Navigation latérale affiche toutes les sections
- [ ] Page "Démarrage rapide" affiche les blocs de code
- [ ] Page "Authentification" affiche le flux et les exemples curl
- [ ] Page "Référence API" affiche le Swagger UI (nécessite le backend lancé sur 8000)
- [ ] Page "Changelog" affiche la version 1.0.0

Arrêter le serveur avec `Ctrl+C` une fois vérifié.

- [ ] **Step 4 : Commiter**

```bash
cd backend
git add docs/docs/changelog.md
git commit -m "docs: add changelog page and complete MkDocs site"
```

---

### Task 8 : Ajouter `backend/docs/` au `.gitignore` et documenter les commandes

**Contexte :** Le dossier `site/` généré par MkDocs ne doit pas être commité. On documente aussi les commandes MkDocs dans le README backend existant.

**Files:**
- Modify: `backend/README.md`
- Verify: `backend/docs/.gitignore`

- [ ] **Step 1 : Vérifier que `site/` est bien ignoré**

```bash
cd backend
git status docs/
```

Résultat attendu : `docs/site/` n'apparaît pas dans les fichiers non-trackés (il est ignoré par `docs/.gitignore`).

- [ ] **Step 2 : Ajouter une section MkDocs au README backend**

Ajouter à la fin de `backend/README.md` :

```markdown
---

## Documentation (MkDocs)

Le site de documentation est dans `backend/docs/`.

### Développement local

```bash
# Lancer le serveur de documentation (live reload)
cd backend/docs
uv run --directory .. mkdocs serve --dev-addr 0.0.0.0:8001
```

Ouvrir http://localhost:8001. Le Swagger UI sur la page "Référence API" nécessite le backend lancé sur le port 8000.

### Build statique

```bash
cd backend/docs
uv run --directory .. mkdocs build
# → génère backend/docs/site/
```

### Déploiement GitHub Pages

```bash
cd backend/docs
uv run --directory .. mkdocs gh-deploy --force
```
```

- [ ] **Step 3 : Commiter**

```bash
cd backend
git add README.md
git commit -m "docs(readme): add MkDocs commands to backend README"
```

---

## Self-Review

### Couverture du spec

| Exigence spec | Tâche |
|---------------|-------|
| MkDocs dans `backend/docs/`, thème readthedocs | Task 3 |
| Dépendance `mkdocs>=1.6` dans pyproject.toml | Task 2 |
| `docs_url="/api/docs"`, `redoc_url="/api/redoc"` | Task 1 |
| Désactiver Swagger natif en production | Task 1 |
| `/openapi.json` toujours actif | Task 1 (testé) |
| `index.md`, `getting-started.md` | Task 4 |
| `authentication.md` avec exemples curl | Task 5 |
| `api-reference.md` avec Swagger UI CDN | Task 6 |
| `changelog.md` | Task 7 |
| Navigation MkDocs complète | Task 3 |
| `site/` gitignored | Task 8 |
| Commandes documentées dans README | Task 8 |

### Scan des placeholders

- `<repo-url>` dans `getting-started.md` → intentionnel, l'URL du repo n'est pas connue
- `http://localhost:8000/openapi.json` dans `api-reference.md` → intentionnel, avec note pour prod
- Pas de TBD, TODO, "implement later", ou "similar to Task N"

### Cohérence des types

- `APP_ENV` importé depuis `core.config` — déjà présent dans `main.py`
- `uv run --directory ..` depuis `backend/docs/` pointe vers `backend/` — cohérent avec la structure uv
- Toutes les URLs API référencent `/api/v1/auth/...` — cohérent avec `API_V1_PREFIX` du config
