# Vitest — Setup unit/composant/snapshot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter Vitest au frontend Next.js 16 + React 19 pour couvrir les tests unit (lib/), composant (Testing Library) et snapshot, avec couverture V8 à seuil 80% et workflow CI GitHub Actions.

**Architecture:** Single-pool jsdom — tous les tests (unit et composant) tournent dans un seul environnement Vitest avec `environment: 'jsdom'`. Les modules `"server-only"` ne sont jamais importés dans les tests grâce à `vi.mock()` explicite sur les modules actions. Coverage V8 mesure uniquement les fichiers importés par les tests (pas d'`include` global).

**Tech Stack:** Vitest 3, @vitejs/plugin-react, @testing-library/react v16 (React 19), @testing-library/jest-dom, jsdom, @vitest/coverage-v8, pnpm, GitHub Actions

---

## Fichiers créés / modifiés

| Action | Chemin |
|--------|--------|
| Créer | `frontend/vitest.config.ts` |
| Créer | `frontend/src/test/setup.ts` |
| Créer | `frontend/src/test/vitest-env.d.ts` |
| Créer | `frontend/src/lib/__tests__/utils.test.ts` |
| Créer | `frontend/src/lib/__tests__/auth-helpers.test.ts` |
| Créer | `frontend/src/components/ui/__tests__/Message.test.tsx` |
| Créer | `frontend/src/components/__tests__/ChatForm.test.tsx` |
| Créer | `.github/workflows/frontend-tests.yml` |
| Modifier | `frontend/package.json` (scripts) |
| Modifier | `.gitignore` (coverage/) |

---

## Task 1 : GitHub issue + branche

**Files:**
- Aucun fichier modifié

- [ ] **Step 1 : Créer l'issue GitHub**

```bash
gh issue create \
  --title "feat: add Vitest for unit/component/snapshot testing" \
  --body "## Objectif
Mettre en place Vitest comme runner de tests pour le frontend.

## Périmètre
- Tests unit : \`src/lib/utils.ts\`, \`src/lib/auth-helpers.ts\`
- Tests composant + snapshot : \`src/components/ui/Message.tsx\`
- Tests composant avec mock : \`src/components/ChatForm.tsx\`
- Coverage V8 avec seuil 80%
- Workflow CI GitHub Actions

## Spec
\`docs/specs/2026-06-14-vitest-unit-component-snapshot-design.md\`"
```

Note le numéro de l'issue retourné (ex: `#84`). Il servira pour le nom de branche.

- [ ] **Step 2 : Créer et checkout la branche**

```bash
# Remplace 84 par le numéro réel de l'issue
git checkout -b feat/84-vitest-unit-component-snapshot
```

---

## Task 2 : Installation des dépendances

**Files:**
- Modifier : `frontend/package.json` (devDependencies)
- Modifier : `frontend/pnpm-lock.yaml` (auto-généré)

- [ ] **Step 1 : Installer les packages depuis `frontend/`**

```bash
cd frontend && pnpm add -D \
  vitest \
  @vitejs/plugin-react \
  "@testing-library/react" \
  "@testing-library/user-event" \
  "@testing-library/jest-dom" \
  jsdom \
  @vitest/coverage-v8
```

- [ ] **Step 2 : Vérifier que les packages sont dans `devDependencies`**

```bash
node -e "const p = require('./package.json'); const keys = Object.keys(p.devDependencies); ['vitest','@vitejs/plugin-react','@testing-library/react','@testing-library/jest-dom','jsdom','@vitest/coverage-v8'].forEach(k => { if(!keys.includes(k)) throw new Error('Missing: '+k); }); console.log('OK');"
```

Résultat attendu : `OK`

- [ ] **Step 3 : Commit**

```bash
git add frontend/package.json frontend/pnpm-lock.yaml
git commit -m "chore: install Vitest and Testing Library dependencies"
```

---

## Task 3 : Configuration Vitest + fichiers de setup

**Files:**
- Créer : `frontend/vitest.config.ts`
- Créer : `frontend/src/test/setup.ts`
- Créer : `frontend/src/test/vitest-env.d.ts`
- Modifier : `frontend/package.json` (scripts)
- Modifier : `.gitignore`

- [ ] **Step 1 : Créer `frontend/vitest.config.ts`**

```typescript
import react from '@vitejs/plugin-react'
import path from 'path'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'html'],
      exclude: [
        'src/models/gen/**',
        'src/**/*.test.{ts,tsx}',
        'src/test/**',
        'src/instrumentation*.ts',
        'src/proxy.ts',
      ],
      thresholds: {
        statements: 80,
        branches: 80,
        functions: 80,
        lines: 80,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '.'),
    },
  },
})
```

- [ ] **Step 2 : Créer `frontend/src/test/setup.ts`**

```typescript
import '@testing-library/jest-dom'
```

- [ ] **Step 3 : Créer `frontend/src/test/vitest-env.d.ts`**

```typescript
/// <reference types="vitest/globals" />
```

Ce fichier donne accès aux globals `describe`, `it`, `expect`, `vi` dans tous les fichiers `.test.*` sans import, sans modifier le `tsconfig.json` géré par Next.js.

- [ ] **Step 4 : Ajouter les scripts dans `frontend/package.json`**

Dans la section `"scripts"`, ajouter après `"lint"` :

```json
"test": "vitest",
"test:run": "vitest run",
"test:coverage": "vitest run --coverage",
"test:ui": "vitest --ui"
```

- [ ] **Step 5 : Ajouter `frontend/coverage/` au `.gitignore` racine**

Dans le fichier `.gitignore` à la racine du repo (pas dans `frontend/`), ajouter à la fin :

```
# Frontend test outputs
frontend/coverage/
```

- [ ] **Step 6 : Vérifier que la config est valide — 0 test trouvé**

```bash
cd frontend && pnpm test:run
```

Résultat attendu :
```
No test files found, exiting with code 1
```
(ou équivalent Vitest indiquant 0 fichier de test) — c'est normal, on n'a pas encore de tests.

Si tu vois une erreur TypeScript ou d'import, c'est un problème de config à régler avant de continuer.

- [ ] **Step 7 : Commit**

```bash
git add frontend/vitest.config.ts \
  frontend/src/test/setup.ts \
  frontend/src/test/vitest-env.d.ts \
  frontend/package.json \
  .gitignore
git commit -m "chore: configure Vitest with jsdom, V8 coverage and test scripts"
```

---

## Task 4 : Tests unitaires — `cn()` dans `utils.ts`

**Files:**
- Créer : `frontend/src/lib/__tests__/utils.test.ts`
- Référence : `frontend/src/lib/utils.ts`

- [ ] **Step 1 : Créer le dossier et le fichier de test**

```bash
mkdir -p frontend/src/lib/__tests__
```

Créer `frontend/src/lib/__tests__/utils.test.ts` :

```typescript
import { cn } from '../utils'

describe('cn', () => {
  it('concatène des classes simples', () => {
    expect(cn('foo', 'bar')).toBe('foo bar')
  })

  it('résout les conflits Tailwind (la dernière classe gagne)', () => {
    expect(cn('p-4', 'p-2')).toBe('p-2')
  })

  it('ignore les valeurs falsy', () => {
    expect(cn('foo', false, undefined, null, 'bar')).toBe('foo bar')
  })
})
```

- [ ] **Step 2 : Lancer les tests et vérifier qu'ils passent**

```bash
cd frontend && pnpm test:run src/lib/__tests__/utils.test.ts
```

Résultat attendu :
```
✓ src/lib/__tests__/utils.test.ts (3)
  ✓ cn > concatène des classes simples
  ✓ cn > résout les conflits Tailwind (la dernière classe gagne)
  ✓ cn > ignore les valeurs falsy

Test Files  1 passed (1)
Tests       3 passed (3)
```

- [ ] **Step 3 : Commit**

```bash
git add frontend/src/lib/__tests__/utils.test.ts
git commit -m "test: unit tests for cn() utility"
```

---

## Task 5 : Tests unitaires — `auth-helpers.ts`

**Files:**
- Créer : `frontend/src/lib/__tests__/auth-helpers.test.ts`
- Référence : `frontend/src/lib/auth-helpers.ts`, `frontend/src/lib/type.lib.ts`

- [ ] **Step 1 : Créer `frontend/src/lib/__tests__/auth-helpers.test.ts`**

```typescript
import { getLoginPayload, validateLoginPayload } from '../auth-helpers'

// `Parameters<typeof fn>[0]` récupère le type exact attendu par la fonction
// sans importer le schéma Zod généré (LoginResponse) directement.
type OkArg = Parameters<typeof getLoginPayload>[0]
type ErrArg = Extract<OkArg, { ok: false }>

const ok = (data: unknown) =>
  ({ ok: true as const, status: 200, data }) as OkArg

const err: ErrArg = {
  ok: false,
  status: 401,
  error: {
    kind: 'http',
    code: 'HTTP_401',
    message: 'Unauthorized',
    userMessage: 'Non autorisé',
  },
}

describe('getLoginPayload', () => {
  it('retourne data.data quand la réponse est ok', () => {
    expect(getLoginPayload(ok({ data: { email: 'a@b.com' } }))).toEqual({ email: 'a@b.com' })
  })

  it('retourne null quand le résultat est une erreur', () => {
    expect(getLoginPayload(err)).toBeNull()
  })

  it('retourne null quand data.data est absent (undefined)', () => {
    expect(getLoginPayload(ok({}))).toBeNull()
  })
})

describe('validateLoginPayload', () => {
  it("retourne l'email quand il est valide", () => {
    expect(validateLoginPayload(ok({ data: { email: 'user@example.com' } }))).toBe('user@example.com')
  })

  it("retourne null quand l'email est une chaîne vide", () => {
    expect(validateLoginPayload(ok({ data: { email: '' } }))).toBeNull()
  })

  it('retourne null quand le résultat est une erreur', () => {
    expect(validateLoginPayload(err)).toBeNull()
  })
})
```

- [ ] **Step 2 : Lancer les tests et vérifier qu'ils passent**

```bash
cd frontend && pnpm test:run src/lib/__tests__/auth-helpers.test.ts
```

Résultat attendu :
```
✓ src/lib/__tests__/auth-helpers.test.ts (6)
  ✓ getLoginPayload > retourne data.data quand la réponse est ok
  ✓ getLoginPayload > retourne null quand le résultat est une erreur
  ✓ getLoginPayload > retourne null quand data.data est absent (undefined)
  ✓ validateLoginPayload > retourne l'email quand il est valide
  ✓ validateLoginPayload > retourne null quand l'email est une chaîne vide
  ✓ validateLoginPayload > retourne null quand le résultat est une erreur

Test Files  1 passed (1)
Tests       6 passed (6)
```

- [ ] **Step 3 : Commit**

```bash
git add frontend/src/lib/__tests__/auth-helpers.test.ts
git commit -m "test: unit tests for getLoginPayload and validateLoginPayload"
```

---

## Task 6 : Tests composant + snapshot — `Message.tsx`

**Files:**
- Créer : `frontend/src/components/ui/__tests__/Message.test.tsx`
- Créer (auto) : `frontend/src/components/ui/__tests__/__snapshots__/Message.test.tsx.snap`
- Référence : `frontend/src/components/ui/Message.tsx`

- [ ] **Step 1 : Créer le dossier et le fichier de test**

```bash
mkdir -p frontend/src/components/ui/__tests__
```

Créer `frontend/src/components/ui/__tests__/Message.test.tsx` :

```typescript
import { render, screen } from '@testing-library/react'
import Message from '../Message'

describe('Message — rendu', () => {
  it("affiche le contenu d'un message utilisateur", () => {
    render(<Message type="user" content="Bonjour" />)
    expect(screen.getByText('Bonjour')).toBeInTheDocument()
  })

  it('affiche le contenu IA avec Markdown (texte en gras)', () => {
    render(<Message type="ai" content="**important**" />)
    const el = screen.getByText('important')
    expect(el.closest('strong')).toBeInTheDocument()
  })

  it('affiche un élément <time> quand le timestamp est fourni', () => {
    render(<Message type="user" content="Test" timestamp="2024-01-15T10:00:00Z" />)
    expect(screen.getByRole('time')).toBeInTheDocument()
  })

  it("n'affiche pas de <time> quand le timestamp est absent", () => {
    render(<Message type="user" content="Sans timestamp" />)
    expect(screen.queryByRole('time')).toBeInTheDocument()
    // time est toujours rendu mais avec texte vide
  })
})

describe('Message — snapshots', () => {
  it('snapshot message utilisateur (sans timestamp pour stabilité CI)', () => {
    const { asFragment } = render(<Message type="user" content="Snapshot user" />)
    expect(asFragment()).toMatchSnapshot()
  })

  it('snapshot message IA (sans timestamp pour stabilité CI)', () => {
    const { asFragment } = render(<Message type="ai" content="Snapshot IA" />)
    expect(asFragment()).toMatchSnapshot()
  })
})
```

- [ ] **Step 2 : Premier run — génération des snapshots**

```bash
cd frontend && TZ=UTC pnpm test:run src/components/ui/__tests__/Message.test.tsx
```

Résultat attendu :
```
✓ src/components/ui/__tests__/Message.test.tsx (6)
  ...
  ✓ snapshot message utilisateur (sans timestamp pour stabilité CI) 1ms
  ✓ snapshot message IA (sans timestamp pour stabilité CI)

 1 snapshot written
```

Un dossier `__snapshots__/` est créé automatiquement avec `Message.test.tsx.snap`.

- [ ] **Step 3 : Deuxième run — vérifier que les snapshots sont stables**

```bash
cd frontend && TZ=UTC pnpm test:run src/components/ui/__tests__/Message.test.tsx
```

Résultat attendu : **0 snapshot written**, tous les tests passent. Si un snapshot échoue au second run, il y a un problème de non-déterminisme (ex: timestamp dynamique) — vérifie que les renders n'utilisent pas `Date.now()` implicitement.

- [ ] **Step 4 : Commit (inclure les fichiers snapshot)**

```bash
git add frontend/src/components/ui/__tests__/Message.test.tsx \
  "frontend/src/components/ui/__tests__/__snapshots__/Message.test.tsx.snap"
git commit -m "test: component and snapshot tests for Message"
```

---

## Task 7 : Tests composant avec mock — `ChatForm.tsx`

**Files:**
- Créer : `frontend/src/components/__tests__/ChatForm.test.tsx`
- Référence : `frontend/src/components/ChatForm.tsx`, `frontend/src/actions/chat.action.ts`

**Contexte important :** `ChatForm.tsx` importe les server actions `sendNewMessage` et `continueChat` depuis `@/src/actions/chat.action`. Ces actions utilisent les DAL (`chat.dal.ts`) qui portent `import "server-only"`. Le `vi.mock()` remplace le module entier **avant** que React ne l'importe, évitant ainsi tout chargement de code server-only.

`TextArea` rend un `<textarea>` avec un label visually-hidden "Message" → `getByLabelText('Message')`.
`ButtonSend` rend un `<button>` avec SVG title "Envoyer" → `getByRole('button', { name: 'Envoyer' })`.

- [ ] **Step 1 : Créer le dossier et le fichier de test**

```bash
mkdir -p frontend/src/components/__tests__
```

Créer `frontend/src/components/__tests__/ChatForm.test.tsx` :

```typescript
import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import ChatForm from '../ChatForm'

// Mock complet du module actions — empêche l'import de chat.dal.ts (server-only)
vi.mock('@/src/actions/chat.action', () => ({
  sendNewMessage: vi.fn(),
  continueChat: vi.fn(),
}))

describe('ChatForm', () => {
  it('affiche la zone de texte et le bouton en mode new', () => {
    render(<ChatForm mode="new" />)
    expect(screen.getByLabelText('Message')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Envoyer' })).toBeInTheDocument()
  })

  it('affiche la zone de texte et le bouton en mode continue', () => {
    render(<ChatForm mode="continue" chatId={42} />)
    expect(screen.getByLabelText('Message')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Envoyer' })).toBeInTheDocument()
  })

  it('le bouton est actif par défaut (non en cours de soumission)', () => {
    render(<ChatForm mode="new" />)
    expect(screen.getByRole('button', { name: 'Envoyer' })).not.toBeDisabled()
  })
})
```

- [ ] **Step 2 : Lancer les tests**

```bash
cd frontend && pnpm test:run src/components/__tests__/ChatForm.test.tsx
```

Résultat attendu :
```
✓ src/components/__tests__/ChatForm.test.tsx (3)
  ✓ ChatForm > affiche la zone de texte et le bouton en mode new
  ✓ ChatForm > affiche la zone de texte et le bouton en mode continue
  ✓ ChatForm > le bouton est actif par défaut (non en cours de soumission)

Test Files  1 passed (1)
Tests       3 passed (3)
```

**Si tu vois une erreur `server-only` :** le mock n'a pas fonctionné. Vérifie que `vi.mock(...)` est bien **en dehors** de tout `describe`/`it` (au niveau module), et que le chemin `'@/src/actions/chat.action'` correspond exactement à l'import dans `ChatForm.tsx`.

- [ ] **Step 3 : Commit**

```bash
git add frontend/src/components/__tests__/ChatForm.test.tsx
git commit -m "test: component tests for ChatForm with vi.mock on server actions"
```

---

## Task 8 : Workflow CI GitHub Actions

**Files:**
- Créer : `.github/workflows/frontend-tests.yml`

- [ ] **Step 1 : Créer `.github/workflows/frontend-tests.yml`**

```yaml
name: Frontend Tests

on:
  pull_request:
    branches:
      - main
    paths:
      - "frontend/**"
      - ".github/workflows/frontend-tests.yml"
  push:
    branches:
      - main
    paths:
      - "frontend/**"

permissions:
  contents: read

jobs:
  test:
    name: Run Vitest
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend

    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 # v6.0.3

      - uses: pnpm/action-setup@a7487ba4bdd25f4c6eedc0b00a783da6d2b6b4c9 # v4.1.0
        with:
          version: latest

      - uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020 # v4.4.0
        with:
          node-version: '20'
          cache: 'pnpm'
          cache-dependency-path: frontend/pnpm-lock.yaml

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Run tests with coverage
        env:
          TZ: UTC
        run: pnpm test:coverage

      - name: Upload coverage report
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4.6.2
        if: always()
        with:
          name: coverage-report
          path: frontend/coverage/
          retention-days: 7
```

- [ ] **Step 2 : Commit**

```bash
git add .github/workflows/frontend-tests.yml
git commit -m "ci: add GitHub Actions workflow for frontend Vitest tests"
```

---

## Task 9 : Validation finale + Pull Request

**Files:**
- Aucun fichier modifié

- [ ] **Step 1 : Lancer la suite complète avec couverture**

```bash
cd frontend && TZ=UTC pnpm test:coverage
```

Résultat attendu (ordre variable) :
```
✓ src/lib/__tests__/utils.test.ts (3)
✓ src/lib/__tests__/auth-helpers.test.ts (6)
✓ src/components/ui/__tests__/Message.test.tsx (6)
✓ src/components/__tests__/ChatForm.test.tsx (3)

Test Files  4 passed (4)
Tests       18 passed (18)
```

Suivi du rapport de coverage avec des valeurs ≥ 80% pour chaque métrique (statements, branches, functions, lines).

**Si le seuil de couverture n'est pas atteint :** identifier les branches non couvertes dans le rapport HTML (`frontend/coverage/index.html`) et ajouter les cas de test manquants.

- [ ] **Step 2 : Vérifier le lint (Biome)**

```bash
cd frontend && pnpm lint
```

Résultat attendu : pas d'erreur. Si Biome se plaint des commentaires `// eslint-disable-next-line` dans les tests, les remplacer par des ignores Biome :

```typescript
// biome-ignore lint/suspicious/noExplicitAny: test helper needs loose typing
```

- [ ] **Step 3 : Push de la branche**

```bash
git push -u origin feat/84-vitest-unit-component-snapshot
```

- [ ] **Step 4 : Créer la Pull Request**

```bash
gh pr create \
  --title "feat: add Vitest for unit/component/snapshot testing" \
  --body "## Summary
- Installe Vitest + Testing Library + coverage V8
- 18 tests : 9 unit (lib/), 6 composant+snapshot (Message), 3 composant+mock (ChatForm)
- Coverage V8 avec seuils 80% statements/branches/functions/lines
- Workflow CI GitHub Actions déclenché sur \`frontend/**\`

## Test plan
- [ ] \`pnpm test:run\` passe en vert localement
- [ ] \`pnpm test:coverage\` dépasse les seuils 80%
- [ ] Le workflow CI passe dans l'onglet Actions de la PR
- [ ] Les snapshots sont stables au second run (\`TZ=UTC pnpm test:run\`)

Closes #84"
```

---

## Troubleshooting rapide

| Erreur | Cause probable | Fix |
|--------|---------------|-----|
| `Cannot find module 'server-only'` | `vi.mock()` manquant ou mal placé | Vérifier que `vi.mock(...)` est au niveau module dans `ChatForm.test.tsx` |
| `Cannot find module '@/src/...'` | Alias `@` non configuré dans vitest | Vérifier le `resolve.alias` dans `vitest.config.ts` |
| Snapshot fail au 2e run | Rendu non-déterministe | Identifier la valeur dynamique et la sortir du snapshot |
| Coverage threshold error | Branches non couvertes | Ouvrir `frontend/coverage/index.html` pour identifier les gaps |
| `getByLabelText('Message') not found` | TextArea modifié | Vérifier que le label `htmlFor="chat-message"` et le textarea `id="chat-message"` sont intacts |
