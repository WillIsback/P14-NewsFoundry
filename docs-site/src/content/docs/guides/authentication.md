---
title: Authentification
description: Système d'authentification JWT et session
---

# Authentification et autorisation

## Architecture

Le système d'authentification repose sur deux couches de JWT :

1. **Backend JWT** (python-jose, HS256) — token d'accès généré par FastAPI
2. **Session cookie** (jose, chiffré) — cookie HTTP-only géré par Next.js

## Flux de connexion

```
Utilisateur → formulaire login → Server Action (auth.action.ts)
    → AuthDAL.postLogin() → POST /api/v1/auth/login [email, password]
    → FastAPI : vérifie email + bcrypt(password)
    → Retourne JWT {sub: email, exp: 30min}
    → Frontend : crée session cookie {userId, expiresAt, accessToken}
    → Redirect vers /home
```

## Backend JWT

- **Algorithme :** HS256
- **Clé :** `SECRET_KEY` (32+ caractères requis en production)
- **Expiration :** configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` (défaut : 30 min)
- **Payload :** `{"sub": email, "exp": timestamp}`

### Dépendance `verify_user`

Tous les endpoints protégés utilisent la dépendance FastAPI `verify_user()` qui :
1. Extrait le token JWT de l'en-tête `Authorization: Bearer <token>`
2. Vérifie la signature et l'expiration
3. Charge l'utilisateur depuis la base de données
4. Retourne l'objet `User` ou lève une exception 401

## Sécurité des mots de passe

- **Hachage :** bcrypt via `hash_password()` / `verify_password()`
- **Protection anti-énumération :** utilisation d'un hash bcrypt factice (`DUMMY_BCRYPT_HASH`) pour les utilisateurs inexistants, garantissant un temps de vérification constant quelle que soit l'existence du compte

## Session frontend

- **Cookie :** HTTP-only, créé côté serveur via Next.js `cookies()`
- **Chiffrement :** AES via la librairie `jose` avec `SESSION_SECRET`
- **Payload :** `{userId: email, expiresAt: ISO date, accessToken: JWT backend}`
- **Expiration :** synchronisée avec l'expiration du JWT backend

### Auto-déconnexion sur 401

`fetch.lib.ts` intercepte les réponses HTTP 401 du backend :
1. Supprime le cookie de session
2. Redirige vers `/login`

## Autorisation — Isolation des données

Les endpoints de discussion vérifient que l'utilisateur courant est bien le propriétaire :

```python
# chat_endpoints.py
chat = get_chat_by_id_sync(chat_id)
if not chat or chat.user_id != current_user.id:
    raise HTTPException(status_code=404, detail="Chat not found")
```

Un code 404 est retourné dans tous les cas (chat inexistant ou non possédé) pour ne pas révéler l'existence de discussions appartenant à d'autres utilisateurs.

## Tests d'autorisation

Deux tests dédiés dans `test_chats_authorization.py` :

1. **test_owner_can_read_their_chat_messages** : vérifie qu'un utilisateur peut accéder à ses propres messages (cas nominal)
2. **test_other_user_cannot_access_or_modify_owner_chat** : vérifie qu'un utilisateur ne peut ni lire ni poster dans les discussions d'un autre utilisateur (réponse 404 dans les deux cas)
