---
title: Gestion des erreurs
description: Stratégie de gestion des erreurs frontend et backend
---

# Gestion des erreurs

L'application gère les erreurs à tous les niveaux de la stack, de l'appel API externe jusqu'à l'interface utilisateur.

## Backend (FastAPI)

### Gestionnaires d'exceptions globaux (`main.py`)

Trois gestionnaires interceptent toutes les exceptions non gérées :

| Exception | Code HTTP | Code erreur | Détails |
|-----------|-----------|-------------|---------|
| `HTTPException` | Variable | `HTTP_EXCEPTION` | Message d'erreur explicite |
| `RequestValidationError` | 422 | `VALIDATION_ERROR` | Erreurs de validation Pydantic |
| `Exception` | 500 | `INTERNAL_SERVER_ERROR` | Trace complète en debug, type seulement en production |

### Erreurs WorldNewsAPI

Dans la pipeline d'actualités (`core/news/`), les erreurs de l'API WorldNewsAPI sont gérées à chaque étape :
- **Service de recherche** : capture les exceptions réseau, retourne des résultats partiels si possible
- **Étiquetage LLM** : si le LLM échoue, les clusters sont retournés sans étiquettes plutôt que de bloquer toute la pipeline
- **Mode mock** : en environnement non-production, l'API retourne des données fixes pour éviter les rate limits

### Erreurs LLM

Deux niveaux de gestion :

**Dans les endpoints de chat (`chat_endpoints.py`) :**
```python
try:
    result = await asyncio.wait_for(Runner.run(...), timeout=LLM_TIMEOUT_SECONDS)
except asyncio.TimeoutError:
    raise HTTPException(status_code=504, detail="LLM request timed out")
except Exception as exc:
    raise HTTPException(status_code=502, detail="LLM provider error")
```

**Dans les endpoints de revue de presse (`review_endpoints.py`) :**
```python
try:
    llm_output = await call_llm_structured(...)
except asyncio.TimeoutError:
    raise HTTPException(status_code=504, detail="LLM request timed out")
except Exception:
    raise HTTPException(status_code=502, detail="LLM provider error")
```

Le message utilisateur est persisté **avant** l'appel LLM pour éviter la perte de données en cas de timeout ou de déconnexion.

### Rate limiting

Implémenté dans `core/middleware.py` :
- **Limite générale :** 100 requêtes par fenêtre de 60s
- **Limite de connexion :** 5 tentatives par fenêtre de 60s (prévention brute-force)
- Retourne HTTP 429 avec en-tête `Retry-After`

### Journalisation

- Toutes les erreurs LLM sont loguées avec les métadonnées pertinentes (`chat_id`, `base_url`, `model`)
- Sentry capture les erreurs en production avec un échantillonnage différent selon l'environnement :
  - Production : 10%
  - Développement : 100%
  - Test : 0%

## Frontend

### Couche réseau (`fetch.lib.ts`)

Le client HTTP unifié `fetchJson()` gère plusieurs types d'erreurs :

| Situation | Code | Message utilisateur | Action |
|-----------|------|-------------------|--------|
| HTTP 401 | `SESSION_EXPIRED` | — | Suppression du cookie + redirection `/login` |
| HTTP 4xx/5xx | `HTTP_{status}` | `La requete a echoue` | Retourné à l'appelant |
| Timeout | `REQUEST_TIMEOUT` | `Le serveur met trop de temps a repondre` | Retourné à l'appelant |
| Parse JSON | `INVALID_JSON_RESPONSE` | `Le serveur a retourne une reponse invalide` | Retourné à l'appelant |
| Validation Zod | `RESPONSE_SCHEMA_MISMATCH` | `Reponse serveur inattendue` | Retourné à l'appelant |
| Réseau | `NETWORK_ERROR` | `Probleme de connexion, verifiez votre reseau` | Retourné à l'appelant |

### Server Actions

Chaque Server Action retourne un `ServiceResult<T>` typé :
- `{ok: true, data: T}` en cas de succès
- `{ok: false, error: {...}}` en cas d'échec

### Interface utilisateur

- **Notifications :** la librairie `sonner` affiche des toasts pour les erreurs
- **Loaders :** les appels API lents (LLM, recherche d'actualités) affichent un indicateur de chargement
- **Pages d'erreur :**
  - `not-found.tsx` : page 404 personnalisée pour les discussions inexistantes
  - `global-error.tsx` : boundary d'erreur racine (convention Next.js)
  - `ErrorBoundary` : composant React class-based qui capture les erreurs de rendu

### Sentry (monitoring)

- SDK `@sentry/nextjs` sur le frontend
- Capture les exceptions non gérées côté client et serveur
- Source maps uploadées en production pour un debugging précis
