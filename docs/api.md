# API REST

Tous les points d'API sont préfixés par `/api/v1`.

## Format de réponse standard

Toutes les réponses suivent le format uniforme `ApiResponse` :

```json
{
  "success": true,
  "status": 200,
  "message": "Description textuelle",
  "data": { ... } | null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Message technique",
    "details": { ... } | null
  } | null
}
```

## Points d'API

### Santé — `/api/v1/health`

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| GET | `/health` | Non | Vérification de l'état (DB + LLM) |

### Authentification — `/api/v1/auth`

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| POST | `/auth/login` | Non | Connexion avec email/mot de passe |
| GET | `/auth/protected` | Oui | Ressource protégée de test |
| GET | `/auth/users/me` | Oui | Informations de l'utilisateur courant |

### Discussions — `/api/v1/chats`

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| GET | `/chats` | Oui | Liste des discussions de l'utilisateur |
| GET | `/chats/{chat_id}/messages` | Oui | Messages d'une discussion |
| POST | `/chats/message` | Oui | Nouvelle discussion + premier message |
| POST | `/chats/{chat_id}/messages` | Oui | Continuer une discussion |
| POST | `/chats/{chat_id}/review` | Oui | Générer une revue de presse |

### Revues de presse — `/api/v1/reviews`

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| GET | `/reviews` | Oui | Liste des revues de presse |
| POST | `/reviews` | Oui | Créer une revue de presse |
| GET | `/reviews/chats` | Oui | Revues générées depuis des discussions |

### Actualités — `/api/v1/news`

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| POST | `/news/context` | Oui | Récupérer et étiqueter le contexte d'actualités |
| GET | `/news/context/{chat_id}` | Oui | Contexte d'actualités pour une discussion |

## Codes d'erreur

### Erreurs générales

| Code HTTP | Code erreur | Message | Description |
|-----------|-------------|---------|-------------|
| 401 | `HTTP_EXCEPTION` | `Identifiant ou mot de passe incorrect` | Échec d'authentification (message identique quel que soit le champ erroné pour éviter l'énumération) |
| 404 | `HTTP_EXCEPTION` | `Chat not found` | Discussion inexistante ou n'appartenant pas à l'utilisateur |
| 422 | `VALIDATION_ERROR` | `Request validation failed` | Données de requête invalides (détails dans l'objet `details`) |
| 429 | `HTTP_EXCEPTION` | `Rate limit exceeded` | Trop de requêtes (avec en-tête `Retry-After`) |
| 500 | `INTERNAL_SERVER_ERROR` | `An unexpected error occurred` | Erreur interne non gérée |

### Erreurs LLM

| Code HTTP | Code erreur | Message | Description |
|-----------|-------------|---------|-------------|
| 502 | `HTTP_EXCEPTION` | `LLM provider error` | Le fournisseur LLM a retourné une erreur (défaillance réseau, modèle indisponible) |
| 504 | `HTTP_EXCEPTION` | `LLM request timed out` | Le LLM n'a pas répondu dans le délai configuré (60s) |

### Erreurs de requête

| Code HTTP | Code erreur | Message | Description |
|-----------|-------------|---------|-------------|
| 400 | `HTTP_EXCEPTION` | Message spécifique au contexte | Contenu utilisateur invalide (texte vide, trop long, caractères dangereux) |
| 400 | `HTTP_EXCEPTION` | `No messages to generate a review from` | Tentative de générer une revue sans messages |

### Erreurs applicatives

| Code HTTP | Code erreur | Message | Description |
|-----------|-------------|---------|-------------|
| 500 | `HTTP_EXCEPTION` | `Chat creation failed` | Échec de création de la discussion en base de données |
| 502 | `HTTP_EXCEPTION` | `LLM returned an empty response` | Le LLM a retourné une réponse vide pour une revue de presse |

### Proxy MLflow — `/mlflow`, `/static-files`, `/ajax-api`, `/api/2.0`

Le backend expose un reverse proxy vers le service MLflow interne Railway. Il n'est activé que si `MLFLOW_TRACKING_URI`, `ADMIN_EMAIL` et `ADMIN_PASSWORD` sont définis.

**Authentification :** HTTP Basic (email/mot de passe admin). Le navigateur mémorise les credentials automatiquement après la première authentification.

| Route | Méthodes | Description |
|-------|----------|-------------|
| `/mlflow` | GET POST PUT DELETE PATCH HEAD OPTIONS | UI MLflow (racine) |
| `/mlflow/{path}` | GET POST PUT DELETE PATCH HEAD OPTIONS | Sous-chemins de l'UI |
| `/static-files/{path}` | GET HEAD | Assets statiques SPA MLflow |
| `/ajax-api/{path}` | GET POST PUT DELETE PATCH | API REST MLflow |
| `/api/2.0/{path}` | GET POST PUT DELETE PATCH | API REST MLflow v2 |

**Comportement du proxy :** les headers hop-by-hop (`connection`, `transfer-encoding`, etc.) ainsi que `host`, `authorization`, `origin` et `referer` sont supprimés avant le forwarding. La suppression de `Origin` et `Referer` empêche MLflow de bloquer la requête comme cross-origin.

## Documentation interactive

En environnement non-production, la documentation OpenAPI est accessible à :
- Swagger UI : `/api/docs`
- ReDoc : `/api/redoc`
- Spécification OpenAPI : `/api/openapi.json`
