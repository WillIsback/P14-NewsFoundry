# Design : Documentation MkDocs + FastAPI pour NewsFoundry Backend

**Date :** 2026-05-10
**Statut :** Approuvé

---

## Contexte

Le backend NewsFoundry est une API FastAPI (Python 3.13, `uv`) avec un seul router `auth` exposant 3 endpoints. FastAPI génère nativement une spec OpenAPI JSON via `/openapi.json`. Il n'existe pas encore de documentation structurée pour les consommateurs de l'API.

## Objectif

Mettre en place un site de documentation complet avec :

1. Pages narratives (guides d'utilisation, démarrage rapide, authentification)
2. Référence API interactive (Swagger UI) auto-générée depuis le code FastAPI
3. Une route FastAPI dédiée au Swagger natif (dev), et un site MkDocs statique déployable séparément (prod)

## Approche retenue : MkDocs autonome + FastAPI expose `/openapi.json`

MkDocs est un outil indépendant dans `backend/docs/`. Une page Markdown intègre Swagger UI via CDN pointant vers `/openapi.json` servi par FastAPI. FastAPI garde ses routes Swagger natives déplacées sur `/api/docs` pour le dev. MkDocs est buildé séparément et déployé sur GitHub Pages.

## Architecture et structure des fichiers

```
backend/
├── docs/                          ← nouveau dossier MkDocs
│   ├── mkdocs.yml                 ← config MkDocs (thème ReadTheDocs)
│   └── docs/                     ← sources Markdown
│       ├── index.md               ← page d'accueil
│       ├── getting-started.md     ← guide d'installation et démarrage
│       ├── authentication.md      ← guide narratif sur l'auth JWT
│       ├── api-reference.md       ← page Swagger UI intégré via CDN
│       └── changelog.md           ← historique des versions
├── src/
│   └── main.py                    ← docs_url="/api/docs", désactivé en prod
```

## Changements dans FastAPI (`src/main.py`)

- `docs_url="/api/docs"` et `redoc_url="/api/redoc"` — déplacés pour éviter collision
- En production (`APP_ENV=production`) : `docs_url=None, redoc_url=None` — Swagger natif désactivé, `/openapi.json` reste actif
- `/openapi.json` reste toujours public pour alimenter le site MkDocs

## Configuration MkDocs (`backend/docs/mkdocs.yml`)

```yaml
site_name: NewsFoundry API
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

Thème `readthedocs` inclus dans MkDocs par défaut — zéro dépendance supplémentaire.

## Contenu des pages

| Page | Contenu |
|------|---------|
| `index.md` | Présentation de NewsFoundry, liens rapides |
| `getting-started.md` | Prérequis, `uv sync`, variables d'env, lancement serveur |
| `authentication.md` | Flux JWT : login → token → requêtes protégées, exemples `curl` |
| `api-reference.md` | Bloc HTML Swagger UI CDN → `/openapi.json` |
| `changelog.md` | v1.0.0 — endpoints auth initiaux |

## Page `api-reference.md` — bloc HTML clé

```html
<div id="swagger-ui"></div>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist/swagger-ui.css">
<script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
<script>
  SwaggerUIBundle({
    url: "https://<RAILWAY_URL>/openapi.json",
    dom_id: '#swagger-ui',
    presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
    layout: "StandaloneLayout"
  })
</script>
```

En dev, l'URL est `http://localhost:8000/openapi.json`.

## Flux selon l'environnement

### Développement local

```
FastAPI → localhost:8000/api/docs        (Swagger natif, dev only)
         → localhost:8000/openapi.json   (spec JSON live)

MkDocs  → localhost:8001                 (mkdocs serve)
         → /api-reference               (Swagger UI CDN → localhost:8000/openapi.json)
```

Commande : `cd backend/docs && mkdocs serve --dev-addr 0.0.0.0:8001`

### Production

```
Railway  → <url>/openapi.json            (spec JSON publique)
          → /api/docs désactivé          (docs_url=None)

GitHub Pages → site MkDocs statique
             → /api-reference           (Swagger UI CDN → Railway/openapi.json)
```

## Dépendances

Ajouter dans `pyproject.toml` (groupe `dev`) :

```toml
[dependency-groups]
dev = [
    "mkdocs>=1.6",
]
```

Un seul package. Le thème `readthedocs` est inclus dans MkDocs.

## Commandes

```bash
# Installer
uv add --group dev mkdocs

# Développement (live reload)
cd backend/docs && mkdocs serve --dev-addr 0.0.0.0:8001

# Build statique
cd backend/docs && mkdocs build          # → génère site/

# Déploiement GitHub Pages
cd backend/docs && mkdocs gh-deploy --force
```

## Hors-scope

- Plugin `mkdocs-swagger-ui-tag` (approche C rejetée)
- Montage StaticFiles dans FastAPI (approche B rejetée)
- Personnalisation thème (thème ReadTheDocs par défaut retenu)
- Génération automatique de docstrings Python (mkdocstrings)
