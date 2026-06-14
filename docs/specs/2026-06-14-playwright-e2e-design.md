# Design — Tests E2E Playwright

**Date :** 2026-06-14
**Scope :** Frontend Next.js 16 + React 19
**Issue GitHub à créer :** feat: add Playwright E2E tests

---

## Contexte

Le frontend NewsFoundry dispose de tests unitaires et composant via Vitest (issue #101). Cette issue ajoute les tests E2E avec Playwright pour valider les flux utilisateur complets. Une issue séparée couvrira les tests de régression visuelle (comparaison maquettes Figma).

## Décisions structurantes

| Décision | Valeur retenue | Raison |
|---|---|---|
| Mode Next.js | `next build` + `next start` | Comportement identique à la prod |
| Navigateur | Chromium uniquement | CI rapide, extensible plus tard |
| Mock backend | Serveur Express HTTP (port 3001) | Seule approche qui intercepte les fetch server-side |
| Authentification tests | Cookie de session JWT généré par `globalSetup` | Pas de login manuel à chaque test |
| Isolation utilisateur | 2 contextes Playwright (user-a, user-b) avec tokens distincts | Réaliste et simple |

## Architecture

```
frontend/
├── playwright.config.ts
└── e2e/
    ├── global-setup.ts               # Génère user-a.json et user-b.json avant les tests
    ├── mocks/
    │   └── api-server.ts             # Serveur Express mock (port 3001)
    ├── fixtures/
    │   ├── auth.ts                   # Playwright fixture : contextes user-a / user-b
    │   ├── data.ts                   # Données JSON de test (chats, messages, reviews)
    │   └── .auth/                    # storageState générés (gitignorés)
    │       ├── user-a.json
    │       └── user-b.json
    └── tests/
        ├── auth.spec.ts
        ├── chat.spec.ts
        ├── review.spec.ts
        ├── isolation.spec.ts
        └── errors.spec.ts
```

## Stratégie mock backend

Le serveur Express tourne sur `http://localhost:3001`. Next.js le cible via `BACKEND_URL=http://localhost:3001` injecté au démarrage. Le serveur inspecte le header `Authorization: Bearer <token>` pour renvoyer les données du bon utilisateur.

### Utilisateurs fictifs

| | User A | User B |
|---|---|---|
| email | `user-a@test.com` | `user-b@test.com` |
| Bearer token | `mock-token-user-a` | `mock-token-user-b` |
| Chats | Chat #1 ("Discussion IA"), Chat #2 | Chat #3 |
| Accès `/chats/1/messages` | ✅ 200 | ❌ 404 |

### Endpoints mock couverts

```
POST  /auth/login
  → 200 + { data: { access_token: "mock-token-user-a", ... } }   (credentials valides)
  → 401 + { detail: "Invalid credentials" }                       (mauvais mot de passe)

GET   /chats
  → 200 + { data: [{ id: 1, title: "Discussion IA" }, ...] }     (user-a)
  → 200 + { data: [{ id: 3, title: "Mon chat" }] }               (user-b)

POST  /chats
  → 200 + { data: { chat_id: 1 } }

GET   /chats/:id/messages
  → 200 + { data: [user_message, assistant_message] }            (propriétaire)
  → 404                                                           (autre utilisateur)

POST  /chats/:id/messages
  → 200 + { data: { ... } }

GET   /reviews
  → 200 + { data: [{ id: 1, title: "Revue du jour", content: "..." }] }

POST  /reviews/generate/:chatId
  → 200 + { data: { title: "Revue mockée", content: "Contenu de la revue..." } }

GET   /chats/:id/reviews
  → 200 + { data: [] }
```

## Stratégie d'authentification

`globalSetup` génère deux JWT valides avec `jose` (déjà installé dans le projet) signés par `E2E_SESSION_SECRET`. Le payload est identique à ce que produit `createSession()` dans `session.ts` :

```typescript
// Payload du cookie "session"
{
  userId: "user-a@test.com",
  accessToken: "mock-token-user-a",
  expiresAt: "2099-01-01T00:00:00.000Z"
}
```

Next.js accepte ces cookies car ils sont signés avec le même secret. La valeur de `E2E_SESSION_SECRET` est distincte du `SESSION_SECRET` de production.

Les `storageState` JSON (cookies de session) sont sauvegardés dans `e2e/fixtures/.auth/` (gitignorés) et injectés dans les contextes Playwright via la fixture `auth.ts`.

## Scénarios de tests

### `auth.spec.ts`
- Login valide : email + mot de passe corrects → redirect vers `/home`
- Login invalide : mauvais mot de passe → `<p role="status">` contient le message d'erreur
- Déconnexion : click logout → redirect vers `/login`, `/home` inaccessible
- Accès direct `/home` sans session → redirect vers `/login`

### `chat.spec.ts`
- Liste des discussions : `/home` affiche "Discussion IA" et "Chat #2" dans le menu
- Nouveau chat : saisir un message → submit → redirect `/chat/1` → réponse IA affichée
- Reprendre un chat : cliquer "Discussion IA" dans le menu → `/chat/1` → historique visible
- Réponse LLM : le message `role: assistant` apparaît dans la page chat après envoi

### `review.spec.ts`
- Accéder à l'onglet revues (`/home?mode=review`) → liste de revues affichée
- Générer une revue depuis un chat : click "Générer" → titre "Revue mockée" apparaît

### `isolation.spec.ts`
- user-b navigue vers `/chat/1` (appartient à user-a) → page 404 affichée
- user-b voit uniquement ses propres chats dans le menu (Chat #3 uniquement)

### `errors.spec.ts`
- Login avec mauvais mot de passe → message d'erreur visible (`role="status"`)
- Mock retourne 500 sur `/chats` → `ErrorBoundary` affiche un message d'erreur

## Configuration Playwright

**`playwright.config.ts`** :
```typescript
export default defineConfig({
  testDir: './e2e/tests',
  globalSetup: './e2e/global-setup.ts',
  use: {
    baseURL: 'http://localhost:3000',
    storageState: 'e2e/fixtures/.auth/user-a.json',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } }
  ],
  webServer: [
    {
      command: 'node e2e/mocks/api-server.js',
      port: 3001,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'pnpm start',
      port: 3000,
      env: {
        SESSION_SECRET: process.env.SESSION_SECRET!,
        BACKEND_URL: 'http://localhost:3001',
      },
      reuseExistingServer: !process.env.CI,
    },
  ],
})
```

## Workflow CI — `.github/workflows/playwright-e2e.yml`

Fichier séparé de `frontend-tests.yml` (Vitest). Déclenché sur PR et push vers `main` pour les chemins `frontend/**`.

```yaml
steps:
  - actions/checkout
  - actions/setup-node (Node 20)
  - npm install -g pnpm
  - pnpm install --frozen-lockfile
  - pnpm exec playwright install --with-deps chromium
  - pnpm build                                      # next build
    env: SESSION_SECRET, BACKEND_URL=http://localhost:3001
  - pnpm exec playwright test
    env: SESSION_SECRET, BACKEND_URL=http://localhost:3001
  - upload-artifact: playwright-report/ (si toujours)
```

**Secret GitHub à créer :** `E2E_SESSION_SECRET` (valeur générée via `openssl rand -hex 32`, indépendante de la prod).

## Scripts `package.json`

```json
"e2e": "playwright test",
"e2e:ui": "playwright test --ui",
"e2e:headed": "playwright test --headed"
```

## `.gitignore` (racine)

```
e2e/fixtures/.auth/
playwright-report/
test-results/
```

## Dépendances à installer

```bash
pnpm add -D @playwright/test express @types/express
```

`jose` est déjà installé (utilisé par `session.ts`).

## Décisions clés

| Décision | Raison |
|---|---|
| Express mock server (pas MSW) | MSW node adapter n'intercepte pas les fetch d'un process Next.js séparé |
| JWT générés en globalSetup | Évite un vrai login à chaque test, tests plus rapides et stables |
| `E2E_SESSION_SECRET` distinct | Évite d'exposer le secret de production dans les tests |
| `reuseExistingServer: !process.env.CI` | Permet de garder les serveurs actifs en développement local |
| `storageState` user-a par défaut | Les tests fonctionnels n'ont pas à gérer l'auth sauf `auth.spec.ts` |
| `pnpm build` avant les tests CI | Comportement de production, évite les faux positifs liés au dev mode |
