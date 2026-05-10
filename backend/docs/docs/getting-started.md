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
