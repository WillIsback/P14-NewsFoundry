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
