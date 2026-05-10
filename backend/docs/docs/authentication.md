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
  -d "email=user@example.com&password=your_password"
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
    "email": "user@example.com"
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
