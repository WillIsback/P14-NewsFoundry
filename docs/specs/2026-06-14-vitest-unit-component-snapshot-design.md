# Design — Setup Vitest : tests unit, composant & snapshot

**Date :** 2026-06-14
**Scope :** Frontend Next.js 16 + React 19
**Issue GitHub à créer :** feat: add Vitest for unit/component/snapshot testing

---

## Contexte

Le frontend NewsFoundry n'a aucun test automatisé. Ce document spécifie la mise en place de Vitest comme runner de tests couvrant trois types : unit (fonctions pures), composant (React Testing Library), et snapshot. Une future issue séparée couvrira les tests E2E avec Playwright.

## Architecture retenue — Approche A : single-pool jsdom

Un seul `vitest.config.ts` avec `environment: 'jsdom'`. Tous les tests (unit lib/ et composants) tournent dans le même environnement. `vi.mock()` explicite dans chaque fichier de test de composant pour les modules `"server-only"`.

**Approches rejetées :**
- Dual-pool node+jsdom : bénéfice marginal, config plus complexe dès le départ
- Environnement par docblock : incohérence potentielle, trop verbeux

## Périmètre des tests à livrer dans cette issue

| Fichier testé | Type | Méthode |
|---|---|---|
| `src/lib/utils.ts` — `cn()` | Unit | Vitest pur, pas de DOM |
| `src/lib/auth-helpers.ts` — `getLoginPayload`, `validateLoginPayload` | Unit | Vitest pur |
| `src/components/ui/Message.tsx` | Composant + Snapshot | Testing Library |
| `src/components/ChatForm.tsx` | Composant | Testing Library + `vi.mock` |

## Dépendances à installer

```bash
pnpm add -D vitest @vitejs/plugin-react \
  @testing-library/react @testing-library/user-event \
  @testing-library/jest-dom jsdom \
  @vitest/coverage-v8
```

Notes :
- `@testing-library/react` v16+ requis pour React 19
- `@vitest/coverage-v8` : provider natif V8, plus rapide qu'Istanbul
- `@vitejs/plugin-react` : transforme JSX dans Vitest (remplace Babel)

## Structure des fichiers

```
frontend/
├── vitest.config.ts
├── src/
│   ├── test/
│   │   ├── setup.ts               # import @testing-library/jest-dom
│   │   └── vitest-env.d.ts        # /// <reference types="vitest/globals" />
│   ├── lib/
│   │   └── __tests__/
│   │       ├── utils.test.ts
│   │       └── auth-helpers.test.ts
│   └── components/
│       ├── __tests__/
│       │   └── ChatForm.test.tsx
│       └── ui/
│           └── __tests__/
│               └── Message.test.tsx
```

## Configuration — `vitest.config.ts`

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

**Choix coverage :** pas d'`include` explicite → V8 ne mesure que les fichiers effectivement importés par les tests. Les fichiers sans tests n'apparaissent pas à 0% et ne font pas chuter le seuil de 80%.

## Fichiers de setup

**`src/test/setup.ts`**
```typescript
import '@testing-library/jest-dom'
```

**`src/test/vitest-env.d.ts`**
```typescript
/// <reference types="vitest/globals" />
```

Ce fichier évite de modifier `tsconfig.json` (géré par Next.js) pour ajouter les types globaux Vitest.

## Stratégie mock pour `"server-only"`

Les fichiers DAL (`chat.dal.ts`, `auth.dal.ts`) et `fetch.lib.ts` portent `import "server-only"` en tête. Ils ne sont jamais importés directement dans les tests composants grâce à `vi.mock()` sur le module action parent :

```typescript
// En tête de ChatForm.test.tsx — vi.mock est hoisted automatiquement
vi.mock('@/src/actions/chat.action', () => ({
  sendNewMessage: vi.fn(),
  continueChat: vi.fn(),
}))
```

Aucun alias global `"server-only" → module vide` n'est nécessaire.

## Exemples de tests

### `src/lib/__tests__/utils.test.ts`
```typescript
import { cn } from '../utils'

describe('cn', () => {
  it('concatène des classes simples', () => {
    expect(cn('foo', 'bar')).toBe('foo bar')
  })
  it('résout les conflits Tailwind (la dernière gagne)', () => {
    expect(cn('p-4', 'p-2')).toBe('p-2')
  })
  it('ignore les valeurs falsy', () => {
    expect(cn('foo', false, undefined, null, 'bar')).toBe('foo bar')
  })
})
```

### `src/lib/__tests__/auth-helpers.test.ts`
```typescript
import type { ServiceResult } from '../type.lib'
import { getLoginPayload, validateLoginPayload } from '../auth-helpers'

const ok = (data: unknown) =>
  ({ ok: true, status: 200, data }) as ServiceResult<{ data?: { email?: string } }>

const err: ServiceResult<never> = {
  ok: false,
  status: 401,
  error: { kind: 'http', code: 'HTTP_401', message: '', userMessage: '' },
}

describe('getLoginPayload', () => {
  it('retourne data.data quand la réponse est ok', () => {
    expect(getLoginPayload(ok({ data: { email: 'a@b.com' } }))).toEqual({ email: 'a@b.com' })
  })
  it('retourne null quand le résultat est une erreur', () => {
    expect(getLoginPayload(err)).toBeNull()
  })
  it('retourne null quand data.data est absent', () => {
    expect(getLoginPayload(ok({}))).toBeNull()
  })
})

describe('validateLoginPayload', () => {
  it("retourne l'email quand il est valide", () => {
    expect(validateLoginPayload(ok({ data: { email: 'user@example.com' } }))).toBe('user@example.com')
  })
  it("retourne null quand l'email est vide", () => {
    expect(validateLoginPayload(ok({ data: { email: '' } }))).toBeNull()
  })
  it('retourne null quand le résultat est une erreur', () => {
    expect(validateLoginPayload(err)).toBeNull()
  })
})
```

### `src/components/ui/__tests__/Message.test.tsx`
```typescript
import { render, screen } from '@testing-library/react'
import Message from '../Message'

describe('Message — rendu', () => {
  it("affiche le contenu d'un message utilisateur", () => {
    render(<Message type="user" content="Bonjour" />)
    expect(screen.getByText('Bonjour')).toBeInTheDocument()
  })
  it('affiche le contenu IA avec Markdown (gras)', () => {
    render(<Message type="ai" content="**important**" />)
    const el = screen.getByText('important')
    expect(el.closest('strong')).toBeInTheDocument()
  })
  it('affiche un élément <time> quand timestamp fourni', () => {
    render(<Message type="user" content="Test" timestamp="2024-01-15T10:00:00Z" />)
    expect(screen.getByRole('time')).toBeInTheDocument()
  })
})

describe('Message — snapshots', () => {
  it('snapshot message utilisateur', () => {
    const { asFragment } = render(<Message type="user" content="Snapshot user" />)
    expect(asFragment()).toMatchSnapshot()
  })
  it('snapshot message IA', () => {
    const { asFragment } = render(<Message type="ai" content="Snapshot IA" />)
    expect(asFragment()).toMatchSnapshot()
  })
})
```

> Snapshots sans timestamp pour éviter la flakiness liée aux fuseaux horaires.

### `src/components/__tests__/ChatForm.test.tsx`
```typescript
import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import ChatForm from '../ChatForm'

vi.mock('@/src/actions/chat.action', () => ({
  sendNewMessage: vi.fn(),
  continueChat: vi.fn(),
}))

describe('ChatForm', () => {
  it('affiche le formulaire en mode new', () => {
    render(<ChatForm mode="new" />)
    expect(screen.getByRole('form')).toBeInTheDocument()
  })
  it('affiche le formulaire en mode continue', () => {
    render(<ChatForm mode="continue" chatId={42} />)
    expect(screen.getByRole('form')).toBeInTheDocument()
  })
})
```

## Scripts `package.json`

```json
"test": "vitest",
"test:run": "vitest run",
"test:coverage": "vitest run --coverage",
"test:ui": "vitest --ui"
```

## `.gitignore` (racine du projet)

```
# Frontend test outputs
frontend/coverage/
```

## Workflow CI — `.github/workflows/frontend-tests.yml`

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

`TZ: UTC` garantit que les snapshots contenant des timestamps sont identiques entre le runner CI et le poste local (si lancé avec `TZ=UTC pnpm test`).

## Décisions clés

| Décision | Raison |
|---|---|
| Vitest plutôt que Jest | Stack Vite/ESM natif, zéro config Babel, plus rapide |
| Single-pool jsdom | Simplicité, aligné avec la doc Next.js, extensible vers dual-pool si besoin |
| `vi.mock()` par fichier | Explicite, pas d'alias global qui masque les imports server-only |
| Coverage V8 sans `include` global | Évite les 0% sur les fichiers non testés qui feraient échouer les seuils |
| Snapshots sans timestamp | Stabilité cross-timezone entre dev local et CI |
| `vitest-env.d.ts` séparé | Ne touche pas au `tsconfig.json` géré par Next.js |
