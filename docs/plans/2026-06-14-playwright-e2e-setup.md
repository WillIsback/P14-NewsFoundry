# Playwright E2E Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Playwright E2E tests covering the 7 core user flows, with a local Express mock server so CI never calls the real Railway backend.

**Architecture:** An Express HTTP mock server (port 3001) replaces the Railway backend by responding to all DAL fetch calls based on the `Authorization: Bearer` token. `globalSetup` generates three JWT session cookies (user-a, user-b, user-error) signed with `SESSION_SECRET` so Next.js accepts them without a real login. Tests run against a `next build` + `next start` production server on port 3000 with `BACKEND_URL=http://localhost:3001`.

**Tech Stack:** `@playwright/test`, `express`, `@types/express`, `tsx`, `jose` (already installed), Next.js 16, TypeScript strict

**Spec:** `docs/specs/2026-06-14-playwright-e2e-design.md`

---

## Key facts deduced from the codebase (read before implementing)

**Exact API routes called by the DAL:**
- `POST /auth/login` → `{ email, password }` → 200 OK or 422 (wrong credentials show error; 401 causes redirect in fetch.lib.ts — do NOT return 401 for wrong password in mock)
- `GET /chats` → list of `{ id: number, date: string }` — no title field, UI shows "Discussion du [dd/MM/yyyy]"
- `GET /chats/:chatId/messages` → list of `{ id, chat_id, type, content, timestamp }`
- `POST /chats/message` → new chat + first message → redirect to `/chat/:chat_id`
- `POST /chats/:chatId/messages` → continue chat
- `GET /reviews` → list of `{ id, title, description, content }`
- `GET /reviews/chats` → list of chat reviews
- `POST /chats/:chatId/review` → generate review from chat (NOT `/reviews/generate/:chatId`)

**Message types:** `"user"` or `"ai"` (AssistantCard checks `message.type === "ai"`, NOT "assistant")

**Auth redirect:** `fetch.lib.ts` intercepts ALL 401 responses and calls `redirect("/login")`. So when the mock returns 401 on `/chats` for unauthenticated requests, Next.js redirects to `/login` — this is how the "no session" test works.

**Error display:** The ErrorBoundary for the Menu (chats) shows a hidden empty `<aside>` on error — NOT a user-visible message. The ErrorBoundary for **reviews** shows `"Impossible de charger les revues de presse."` — use `/home?mode=review` with user-error for the visible error test.

**UI selectors:**
- Logout: `getByRole("button", { name: "Se deconnecter" })` (SVG `<title>Se deconnecter</title>`)
- Review button: `getByRole("button", { name: "Générer une revue de presse" })`
- Login error: `getByRole("status")` → text "Le formulaire de connexion est invalide"
- Chat link in menu: `getByRole("link", { name: /Discussion du/ })`

**Sentry in next build:** `next.config.ts` uses `withSentryConfig`. Add `SENTRY_UPLOAD_SOURCEMAPS=false` to build env to prevent upload attempts without auth token.

---

## File structure

```
frontend/
├── playwright.config.ts                      # Create
├── e2e/
│   ├── global-setup.ts                       # Create — generates .auth/*.json
│   ├── mocks/
│   │   └── api-server.ts                     # Create — Express mock on port 3001
│   ├── fixtures/
│   │   ├── data.ts                           # Create — schema-compliant fixture JSON
│   │   ├── auth.ts                           # Create — exports userX storageState paths
│   │   └── .auth/                            # gitignored, created by globalSetup
│   └── tests/
│       ├── auth.spec.ts                      # Create
│       ├── chat.spec.ts                      # Create
│       ├── review.spec.ts                    # Create
│       ├── isolation.spec.ts                 # Create
│       └── errors.spec.ts                    # Create
├── package.json                              # Modify — add e2e scripts
.github/workflows/playwright-e2e.yml          # Create
.gitignore (root)                             # Modify — add playwright outputs
```

---

## Task 1: Install dependencies + playwright.config.ts + scripts

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/playwright.config.ts`
- Modify: root `.gitignore`

- [ ] **Step 1: Install Playwright and mock server dependencies**

Run from `frontend/`:
```bash
pnpm add -D @playwright/test express @types/express tsx
pnpm exec playwright install --with-deps chromium
```

Expected: installs packages, downloads Chromium (~150 MB first time)

- [ ] **Step 2: Create `frontend/playwright.config.ts`**

```typescript
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
	testDir: "./e2e/tests",
	globalSetup: "./e2e/global-setup.ts",
	fullyParallel: true,
	forbidOnly: !!process.env.CI,
	retries: process.env.CI ? 1 : 0,
	timeout: 30_000,
	reporter: [["html", { outputFolder: "playwright-report" }]],
	use: {
		baseURL: "http://localhost:3000",
		storageState: "e2e/fixtures/.auth/user-a.json",
		trace: "on-first-retry",
	},
	projects: [
		{ name: "chromium", use: { ...devices["Desktop Chrome"] } },
	],
	webServer: [
		{
			command: "pnpm exec tsx e2e/mocks/api-server.ts",
			port: 3001,
			reuseExistingServer: !process.env.CI,
			stdout: "pipe",
			stderr: "pipe",
		},
		{
			command: "pnpm start",
			port: 3000,
			env: {
				SESSION_SECRET: process.env.SESSION_SECRET ?? "dev-test-secret",
				BACKEND_URL: "http://localhost:3001",
				NODE_ENV: "production",
			},
			reuseExistingServer: !process.env.CI,
			stdout: "pipe",
			stderr: "pipe",
		},
	],
});
```

- [ ] **Step 3: Add scripts to `frontend/package.json`**

Add these 3 entries to the `"scripts"` object:
```json
"e2e": "playwright test",
"e2e:local": "pnpm build && playwright test",
"e2e:headed": "playwright test --headed"
```

- [ ] **Step 4: Add Playwright outputs to root `.gitignore`**

Append to `.gitignore` at the repo root:
```
# Playwright E2E
frontend/e2e/fixtures/.auth/
frontend/playwright-report/
frontend/test-results/
```

- [ ] **Step 5: Verify Playwright is found**

Run from `frontend/`:
```bash
pnpm exec playwright --version
```
Expected output: `Version X.Y.Z`

- [ ] **Step 6: Commit**

```bash
git add frontend/playwright.config.ts frontend/package.json .gitignore frontend/pnpm-lock.yaml
git commit -m "feat: install Playwright and configure playwright.config.ts"
```

---

## Task 2: Fixture data

**Files:**
- Create: `frontend/e2e/fixtures/data.ts`

- [ ] **Step 1: Create `frontend/e2e/fixtures/data.ts`**

This file contains schema-compliant fixtures matching the Zod schemas in `src/models/gen/backend.zod.ts`.

```typescript
export const USER_A_EMAIL = "user-a@test.com";
export const USER_B_EMAIL = "user-b@test.com";
export const USER_ERROR_EMAIL = "user-error@test.com";

export const TOKEN_USER_A = "mock-token-user-a";
export const TOKEN_USER_B = "mock-token-user-b";
export const TOKEN_ERROR = "mock-token-error";

export const PASSWORD_OK = "password-a";
export const PASSWORD_WRONG = "wrong-password";

export const loginOkResponse = {
	success: true,
	status: 200,
	message: "Login successful",
	data: {
		access_token: TOKEN_USER_A,
		token_type: "bearer",
		email: USER_A_EMAIL,
	},
};

export const chatsUserA = {
	success: true,
	status: 200,
	message: "Chats retrieved",
	data: [
		{ id: 1, date: "2024-01-15T10:00:00Z" },
		{ id: 2, date: "2024-01-10T09:00:00Z" },
	],
};

export const chatsUserB = {
	success: true,
	status: 200,
	message: "Chats retrieved",
	data: [{ id: 3, date: "2024-01-12T14:00:00Z" }],
};

export const messagesChat1 = {
	success: true,
	status: 200,
	message: "Messages retrieved",
	data: [
		{
			id: 1,
			chat_id: 1,
			type: "user",
			content: "Quelles sont les dernières nouvelles ?",
			timestamp: "2024-01-15T10:01:00Z",
		},
		{
			id: 2,
			chat_id: 1,
			type: "ai",
			content: "Voici un résumé des dernières nouvelles du moment.",
			timestamp: "2024-01-15T10:01:30Z",
		},
	],
};

export const newChatResponse = {
	success: true,
	status: 201,
	message: "Chat created",
	data: {
		chat_id: 1,
		message: {
			id: 3,
			chat_id: 1,
			type: "ai",
			content: "Voici ma réponse IA à votre question.",
			timestamp: "2024-01-15T10:02:00Z",
		},
		context: {
			used_tokens: 100,
			limit_tokens: 4096,
			usage_ratio: 0.024,
			was_compacted: false,
		},
	},
};

export const continueChatResponse = {
	success: true,
	status: 200,
	message: "Message sent",
	data: {
		chat_id: 1,
		message: {
			id: 4,
			chat_id: 1,
			type: "ai",
			content: "Voici ma réponse IA à votre question de suivi.",
			timestamp: "2024-01-15T10:03:00Z",
		},
		context: {
			used_tokens: 200,
			limit_tokens: 4096,
			usage_ratio: 0.049,
			was_compacted: false,
		},
	},
};

export const reviewsResponse = {
	success: true,
	status: 200,
	message: "Reviews retrieved",
	data: [
		{
			id: 1,
			title: "Revue du jour",
			description: "2024-01-15T10:00:00Z",
			content: "Contenu de la revue de presse.",
		},
	],
};

export const chatReviewsResponse = {
	success: true,
	status: 200,
	message: "Chat reviews retrieved",
	data: [],
};

export const generateReviewResponse = {
	success: true,
	status: 201,
	message: "Review generated",
	data: {
		id: 2,
		title: "Revue mockée",
		description: "2024-01-15T10:05:00Z",
		content: "Contenu de la revue mockée.",
		chat_id: 1,
		date: "2024-01-15T10:05:00Z",
	},
};
```

- [ ] **Step 2: Verify TypeScript**

Run from `frontend/`:
```bash
pnpm exec tsc --noEmit --skipLibCheck
```
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/e2e/fixtures/data.ts
git commit -m "feat: add E2E fixture data"
```

---

## Task 3: Express mock API server

**Files:**
- Create: `frontend/e2e/mocks/api-server.ts`

- [ ] **Step 1: Create `frontend/e2e/mocks/api-server.ts`**

```typescript
import express from "express";
import {
	TOKEN_ERROR,
	TOKEN_USER_A,
	TOKEN_USER_B,
	USER_A_EMAIL,
	PASSWORD_OK,
	chatReviewsResponse,
	chatsUserA,
	chatsUserB,
	continueChatResponse,
	generateReviewResponse,
	loginOkResponse,
	messagesChat1,
	newChatResponse,
	reviewsResponse,
} from "../fixtures/data.js";

const app = express();
app.use(express.json());

function extractToken(req: express.Request): string | null {
	const auth = req.headers.authorization;
	if (!auth?.startsWith("Bearer ")) return null;
	return auth.slice(7);
}

function requireAuth(
	req: express.Request,
	res: express.Response,
): string | null {
	const token = extractToken(req);
	if (!token) {
		res.status(401).json({ detail: "Not authenticated" });
		return null;
	}
	if (token === TOKEN_ERROR) {
		res.status(500).json({ detail: "Internal server error" });
		return null;
	}
	return token;
}

// POST /auth/login
app.post("/auth/login", (req, res) => {
	const body = req.body as { email?: string; password?: string };
	if (body.email === USER_A_EMAIL && body.password === PASSWORD_OK) {
		res.json(loginOkResponse);
	} else {
		res.status(422).json({ detail: [] });
	}
});

// GET /chats
app.get("/chats", (req, res) => {
	const token = requireAuth(req, res);
	if (!token) return;
	if (token === TOKEN_USER_A) {
		res.json(chatsUserA);
	} else if (token === TOKEN_USER_B) {
		res.json(chatsUserB);
	} else {
		res.status(401).json({ detail: "Unknown token" });
	}
});

// POST /chats/message — new chat
app.post("/chats/message", (req, res) => {
	const token = requireAuth(req, res);
	if (!token) return;
	res.status(201).json(newChatResponse);
});

// GET /chats/:chatId/messages
app.get("/chats/:chatId/messages", (req, res) => {
	const token = requireAuth(req, res);
	if (!token) return;
	const chatId = Number(req.params.chatId);
	// user-b cannot access chats 1 or 2 (belong to user-a)
	if (token === TOKEN_USER_B && (chatId === 1 || chatId === 2)) {
		res.status(404).json({ detail: "Not found" });
		return;
	}
	if (chatId === 1) {
		res.json(messagesChat1);
	} else {
		res.status(404).json({ detail: "Not found" });
	}
});

// POST /chats/:chatId/messages — continue chat
app.post("/chats/:chatId/messages", (req, res) => {
	const token = requireAuth(req, res);
	if (!token) return;
	res.json(continueChatResponse);
});

// POST /chats/:chatId/review — generate review
app.post("/chats/:chatId/review", (req, res) => {
	const token = requireAuth(req, res);
	if (!token) return;
	res.status(201).json(generateReviewResponse);
});

// GET /reviews
app.get("/reviews", (req, res) => {
	const token = requireAuth(req, res);
	if (!token) return;
	res.json(reviewsResponse);
});

// GET /reviews/chats
app.get("/reviews/chats", (req, res) => {
	const token = requireAuth(req, res);
	if (!token) return;
	res.json(chatReviewsResponse);
});

const server = app.listen(3001, () => {
	console.log("[mock-api] Server running on http://localhost:3001");
});

process.on("SIGTERM", () => server.close());
process.on("SIGINT", () => server.close());
```

- [ ] **Step 2: Smoke test the mock server**

In one terminal from `frontend/`:
```bash
pnpm exec tsx e2e/mocks/api-server.ts
```
Expected: `[mock-api] Server running on http://localhost:3001`

In another terminal:
```bash
curl -s -X POST http://localhost:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user-a@test.com","password":"password-a"}' | python3 -m json.tool
```
Expected: JSON with `"success": true` and `"access_token": "mock-token-user-a"`

```bash
curl -s http://localhost:3001/chats \
  -H "Authorization: Bearer mock-token-user-a" | python3 -m json.tool
```
Expected: JSON with `"data": [{"id": 1, ...}, {"id": 2, ...}]`

Stop the server with Ctrl+C.

- [ ] **Step 3: Commit**

```bash
git add frontend/e2e/mocks/api-server.ts
git commit -m "feat: add Express mock API server for E2E tests"
```

---

## Task 4: Global setup + auth fixtures

**Files:**
- Create: `frontend/e2e/global-setup.ts`
- Create: `frontend/e2e/fixtures/auth.ts`

- [ ] **Step 1: Create `frontend/e2e/global-setup.ts`**

This generates the three `storageState` JSON files that Playwright uses to authenticate browsers. Uses `jose` which is already installed in `frontend/node_modules/jose`.

```typescript
import fs from "node:fs/promises";
import path from "node:path";
import { SignJWT } from "jose";

const SECRET = process.env.SESSION_SECRET;
if (!SECRET) {
	throw new Error("SESSION_SECRET env var is required for E2E tests");
}

const encodedKey = new TextEncoder().encode(SECRET);

async function generateSessionCookie(
	userId: string,
	accessToken: string,
): Promise<string> {
	const expiresAt = new Date("2099-01-01T00:00:00.000Z");
	return new SignJWT({
		userId,
		accessToken,
		expiresAt: expiresAt.toISOString(),
	})
		.setProtectedHeader({ alg: "HS256" })
		.setIssuedAt()
		.setExpirationTime(Math.floor(expiresAt.getTime() / 1000))
		.sign(encodedKey);
}

async function writeStorageState(
	filePath: string,
	sessionJwt: string,
): Promise<void> {
	const state = {
		cookies: [
			{
				name: "session",
				value: sessionJwt,
				domain: "localhost",
				path: "/",
				expires: 4_070_908_800,
				httpOnly: true,
				secure: false,
				sameSite: "Lax" as const,
			},
		],
		origins: [],
	};
	await fs.mkdir(path.dirname(filePath), { recursive: true });
	await fs.writeFile(filePath, JSON.stringify(state, null, 2));
}

export default async function globalSetup(): Promise<void> {
	const authDir = "e2e/fixtures/.auth";

	const userAJwt = await generateSessionCookie(
		"user-a@test.com",
		"mock-token-user-a",
	);
	const userBJwt = await generateSessionCookie(
		"user-b@test.com",
		"mock-token-user-b",
	);
	const userErrorJwt = await generateSessionCookie(
		"user-error@test.com",
		"mock-token-error",
	);

	await writeStorageState(`${authDir}/user-a.json`, userAJwt);
	await writeStorageState(`${authDir}/user-b.json`, userBJwt);
	await writeStorageState(`${authDir}/user-error.json`, userErrorJwt);

	console.log("[globalSetup] Auth storage states generated in", authDir);
}
```

- [ ] **Step 2: Create `frontend/e2e/fixtures/auth.ts`**

This exports path constants for the three storageState files for use in spec files.

```typescript
export const USER_A_STATE = "e2e/fixtures/.auth/user-a.json";
export const USER_B_STATE = "e2e/fixtures/.auth/user-b.json";
export const USER_ERROR_STATE = "e2e/fixtures/.auth/user-error.json";

export const NO_AUTH_STATE = { cookies: [], origins: [] } as const;
```

- [ ] **Step 3: Smoke test globalSetup**

Run from `frontend/`:
```bash
SESSION_SECRET=my-test-secret pnpm exec tsx e2e/global-setup.ts
```
Expected:
```
[globalSetup] Auth storage states generated in e2e/fixtures/.auth
```

Verify files exist:
```bash
ls e2e/fixtures/.auth/
```
Expected: `user-a.json  user-b.json  user-error.json`

Inspect one file:
```bash
cat e2e/fixtures/.auth/user-a.json
```
Expected: JSON with `"cookies": [{"name": "session", "value": "eyJ..."}]`

- [ ] **Step 4: Commit**

```bash
git add frontend/e2e/global-setup.ts frontend/e2e/fixtures/auth.ts
git commit -m "feat: add E2E globalSetup (JWT session generation) and auth fixtures"
```

---

## Task 5: `auth.spec.ts`

**Files:**
- Create: `frontend/e2e/tests/auth.spec.ts`

- [ ] **Step 1: Create `frontend/e2e/tests/auth.spec.ts`**

```typescript
import { expect, test } from "@playwright/test";
import { NO_AUTH_STATE } from "../fixtures/auth.js";

// All tests in this file bypass the default user-a storageState
test.use({ storageState: NO_AUTH_STATE });

test("login valide : redirige vers /home", async ({ page }) => {
	await page.goto("/login");
	await page.getByLabel("Adresse email").fill("user-a@test.com");
	await page.getByLabel("Mot de passe").fill("password-a");
	await page.getByRole("button", { name: "Se connecter" }).click();
	await expect(page).toHaveURL("/home");
});

test("login invalide : affiche le message d'erreur", async ({ page }) => {
	await page.goto("/login");
	await page.getByLabel("Adresse email").fill("user-a@test.com");
	await page.getByLabel("Mot de passe").fill("wrong-password");
	await page.getByRole("button", { name: "Se connecter" }).click();
	await expect(page.getByRole("status")).toContainText(
		"Le formulaire de connexion est invalide",
	);
});

test("déconnexion : redirige vers /login", async ({ page }) => {
	// Start authenticated as user-a
	await page.context().addCookies([
		{
			name: "session",
			value: "placeholder",
			domain: "localhost",
			path: "/",
		},
	]);
	// Use a fresh browser context with user-a cookies instead
	const userAState = await import("../fixtures/.auth/user-a.json", {
		assert: { type: "json" },
	});
	await page.context().clearCookies();
	for (const cookie of userAState.cookies) {
		await page.context().addCookies([cookie]);
	}
	await page.goto("/home");
	await page.getByRole("button", { name: "Se deconnecter" }).click();
	await expect(page).toHaveURL("/login");
});

test("accès /home sans session → redirige vers /login", async ({ page }) => {
	await page.goto("/home");
	await expect(page).toHaveURL("/login");
});
```

**Note:** The logout test needs a cookie set. A simpler approach is to run that test with its own storageState override using `test.extend`. Rewrite it as:

```typescript
import { expect, test as base } from "@playwright/test";
import { NO_AUTH_STATE, USER_A_STATE } from "../fixtures/auth.js";

test.use({ storageState: NO_AUTH_STATE });

test("login valide : redirige vers /home", async ({ page }) => {
	await page.goto("/login");
	await page.getByLabel("Adresse email").fill("user-a@test.com");
	await page.getByLabel("Mot de passe").fill("password-a");
	await page.getByRole("button", { name: "Se connecter" }).click();
	await expect(page).toHaveURL("/home");
});

test("login invalide : affiche le message d'erreur", async ({ page }) => {
	await page.goto("/login");
	await page.getByLabel("Adresse email").fill("user-a@test.com");
	await page.getByLabel("Mot de passe").fill("wrong-password");
	await page.getByRole("button", { name: "Se connecter" }).click();
	await expect(page.getByRole("status")).toContainText(
		"Le formulaire de connexion est invalide",
	);
});

test("accès /home sans session → redirige vers /login", async ({ page }) => {
	await page.goto("/home");
	await expect(page).toHaveURL("/login");
});

const authenticatedTest = base.extend({});

authenticatedTest.use({ storageState: USER_A_STATE });

authenticatedTest(
	"déconnexion : redirige vers /login",
	async ({ page }) => {
		await page.goto("/home");
		await page.getByRole("button", { name: "Se deconnecter" }).click();
		await expect(page).toHaveURL("/login");
	},
);
```

- [ ] **Step 2: Build and run only auth tests**

Run from `frontend/` (first time, builds Next.js):
```bash
SESSION_SECRET=my-test-secret pnpm e2e:local --project=chromium --grep "auth"
```

Or run without rebuilding if `.next/` already exists:
```bash
SESSION_SECRET=my-test-secret pnpm e2e --project=chromium e2e/tests/auth.spec.ts
```

Expected: 4/4 tests passing

- [ ] **Step 3: Commit**

```bash
git add frontend/e2e/tests/auth.spec.ts
git commit -m "feat: add E2E auth tests (login, logout, no-session redirect)"
```

---

## Task 6: `chat.spec.ts`

**Files:**
- Create: `frontend/e2e/tests/chat.spec.ts`

- [ ] **Step 1: Create `frontend/e2e/tests/chat.spec.ts`**

Default `storageState` is user-a (set in `playwright.config.ts`).

```typescript
import { expect, test } from "@playwright/test";

test("liste des discussions : affiche les chats de user-a", async ({
	page,
}) => {
	await page.goto("/home");
	// The Chat component renders "Discussion du" + formatted date
	// chatsUserA has dates 2024-01-15 → "15/01/2024" and 2024-01-10 → "10/01/2024"
	const links = page.getByRole("link", { name: /Discussion du/ });
	await expect(links).toHaveCount(2);
});

test("reprendre un chat : navigue vers /chat/1 et affiche l'historique", async ({
	page,
}) => {
	await page.goto("/home");
	// Click the first chat link (id=1, date "15/01/2024")
	await page.getByRole("link", { name: /15\/01\/2024/ }).click();
	await expect(page).toHaveURL("/chat/1");
	// User message and AI message from messagesChat1 fixture
	await expect(
		page.getByText("Quelles sont les dernières nouvelles ?"),
	).toBeVisible();
	await expect(
		page.getByText("Voici un résumé des dernières nouvelles du moment."),
	).toBeVisible();
});

test("nouveau chat : envoie un message et redirige vers /chat/1", async ({
	page,
}) => {
	await page.goto("/home");
	const textarea = page.getByRole("textbox", { name: /message/i });
	await textarea.fill("Quelle est l'actualité du jour ?");
	await page.getByRole("button", { name: /envoyer/i }).click();
	// sendNewMessage redirects to /chat/:chat_id (chat_id=1 from newChatResponse fixture)
	await expect(page).toHaveURL("/chat/1");
});

test("réponse LLM : le message IA apparaît dans la page chat", async ({
	page,
}) => {
	await page.goto("/chat/1");
	// AI message from messagesChat1 fixture (type: "ai")
	await expect(
		page.getByText("Voici un résumé des dernières nouvelles du moment."),
	).toBeVisible();
});
```

- [ ] **Step 2: Run chat tests**

Run from `frontend/`:
```bash
SESSION_SECRET=my-test-secret pnpm e2e --project=chromium e2e/tests/chat.spec.ts
```

Expected: 4/4 tests passing

- [ ] **Step 3: Commit**

```bash
git add frontend/e2e/tests/chat.spec.ts
git commit -m "feat: add E2E chat tests (list, navigate, new chat, LLM response)"
```

---

## Task 7: `review.spec.ts`

**Files:**
- Create: `frontend/e2e/tests/review.spec.ts`

- [ ] **Step 1: Create `frontend/e2e/tests/review.spec.ts`**

```typescript
import { expect, test } from "@playwright/test";

test("onglet revues : affiche la liste des revues", async ({ page }) => {
	await page.goto("/home?mode=review");
	// PressReview renders <h4>{title}</h4> — "Revue du jour" from reviewsResponse
	await expect(page.getByText("Revue du jour")).toBeVisible();
});

test("générer une revue depuis un chat : redirige vers /home?mode=review", async ({
	page,
}) => {
	await page.goto("/chat/1");
	// ButtonReview is in ChatHeader — visible on the chat page
	await page
		.getByRole("button", { name: "Générer une revue de presse" })
		.click();
	// generateReviewResponse returns id=2 → router.push("/?mode=review#review-2")
	await expect(page).toHaveURL(/mode=review/);
	// After navigation, the generated review title should appear
	await expect(page.getByText("Revue mockée")).toBeVisible();
});
```

- [ ] **Step 2: Run review tests**

Run from `frontend/`:
```bash
SESSION_SECRET=my-test-secret pnpm e2e --project=chromium e2e/tests/review.spec.ts
```

Expected: 2/2 tests passing

- [ ] **Step 3: Commit**

```bash
git add frontend/e2e/tests/review.spec.ts
git commit -m "feat: add E2E review tests (list reviews, generate review)"
```

---

## Task 8: `isolation.spec.ts`

**Files:**
- Create: `frontend/e2e/tests/isolation.spec.ts`

- [ ] **Step 1: Create `frontend/e2e/tests/isolation.spec.ts`**

```typescript
import { expect, test } from "@playwright/test";
import { USER_B_STATE } from "../fixtures/auth.js";

// Override storageState for this entire file
test.use({ storageState: USER_B_STATE });

test("user-b ne voit que ses propres chats", async ({ page }) => {
	await page.goto("/home");
	// chatsUserB fixture has only id=3, date "12/01/2024"
	const links = page.getByRole("link", { name: /Discussion du/ });
	await expect(links).toHaveCount(1);
	await expect(page.getByRole("link", { name: /12\/01\/2024/ })).toBeVisible();
	// user-a's chats should not appear
	await expect(
		page.getByRole("link", { name: /15\/01\/2024/ }),
	).not.toBeVisible();
});

test("user-b ne peut pas accéder au chat de user-a (/chat/1 → 404)", async ({
	page,
}) => {
	await page.goto("/chat/1");
	// fetchMessages(1) returns 404 for user-b → Next.js calls notFound()
	// Next.js renders the nearest not-found.tsx or default 404 page
	await expect(page).toHaveURL("/chat/1");
	// The not-found page exists at src/app/(private)/chat/[slug]/not-found.tsx
	// or Next.js default 404 — check for any indicator of a 404
	const body = page.locator("body");
	// Either a custom not-found or Next.js default 404 contains "404" or "not found"
	await expect(body).not.toContainText("Voici un résumé");
});
```

- [ ] **Step 2: Read `not-found.tsx` to confirm the test selector**

Before running, check what `not-found.tsx` renders:
```bash
cat frontend/src/app/\(private\)/chat/\[slug\]/not-found.tsx
```

If it renders specific text (e.g., "Discussion introuvable"), update the test to assert that text instead of the negative assertion.

- [ ] **Step 3: Run isolation tests**

Run from `frontend/`:
```bash
SESSION_SECRET=my-test-secret pnpm e2e --project=chromium e2e/tests/isolation.spec.ts
```

Expected: 2/2 tests passing

- [ ] **Step 4: Commit**

```bash
git add frontend/e2e/tests/isolation.spec.ts
git commit -m "feat: add E2E user isolation tests"
```

---

## Task 9: `errors.spec.ts`

**Files:**
- Create: `frontend/e2e/tests/errors.spec.ts`

- [ ] **Step 1: Create `frontend/e2e/tests/errors.spec.ts`**

```typescript
import { expect, test } from "@playwright/test";
import { NO_AUTH_STATE, USER_ERROR_STATE } from "../fixtures/auth.js";

test("login invalide : message d'erreur role=status visible", async ({
	page,
}) => {
	test.use({ storageState: NO_AUTH_STATE });
	await page.goto("/login");
	await page.getByLabel("Adresse email").fill("user-a@test.com");
	await page.getByLabel("Mot de passe").fill("bad-password");
	await page.getByRole("button", { name: "Se connecter" }).click();
	// loginUser returns { error: "Le formulaire de connexion est invalide" }
	// LoginPage renders <p role="status">{state.error}</p>
	await expect(page.getByRole("status")).toBeVisible();
	await expect(page.getByRole("status")).toContainText(
		"Le formulaire de connexion est invalide",
	);
});

test(
	"erreur serveur 500 sur /reviews : ErrorBoundary affiche le message d'erreur",
	async ({ page }) => {
		test.use({ storageState: USER_ERROR_STATE });
		// user-error token → mock returns 500 on all authenticated endpoints
		// Navigate to review mode: home page fetches /reviews → 500 → ErrorBoundary
		await page.goto("/home?mode=review");
		// ErrorBoundary fallback for reviews section in home/page.tsx:
		// <p className="text-slate-100">Impossible de charger les revues de presse.</p>
		await expect(
			page.getByText("Impossible de charger les revues de presse."),
		).toBeVisible();
	},
);
```

**Note on `test.use` inside test body:** `test.use` must be at file level or describe level, not inside a test body. Rewrite as separate describe blocks:

```typescript
import { expect, test } from "@playwright/test";
import { NO_AUTH_STATE, USER_ERROR_STATE } from "../fixtures/auth.js";

test.describe("erreur login", () => {
	test.use({ storageState: NO_AUTH_STATE });

	test("login invalide : message d'erreur role=status visible", async ({
		page,
	}) => {
		await page.goto("/login");
		await page.getByLabel("Adresse email").fill("user-a@test.com");
		await page.getByLabel("Mot de passe").fill("bad-password");
		await page.getByRole("button", { name: "Se connecter" }).click();
		await expect(page.getByRole("status")).toBeVisible();
		await expect(page.getByRole("status")).toContainText(
			"Le formulaire de connexion est invalide",
		);
	});
});

test.describe("erreur serveur", () => {
	test.use({ storageState: USER_ERROR_STATE });

	test("erreur 500 sur /reviews : affiche le message ErrorBoundary", async ({
		page,
	}) => {
		await page.goto("/home?mode=review");
		await expect(
			page.getByText("Impossible de charger les revues de presse."),
		).toBeVisible();
	});
});
```

- [ ] **Step 2: Run errors tests**

Run from `frontend/`:
```bash
SESSION_SECRET=my-test-secret pnpm e2e --project=chromium e2e/tests/errors.spec.ts
```

Expected: 2/2 tests passing

- [ ] **Step 3: Run full suite**

Run all tests together:
```bash
SESSION_SECRET=my-test-secret pnpm e2e --project=chromium
```

Expected: 13/13 tests passing (4 auth + 4 chat + 2 review + 2 isolation + 2 errors - 1 auth already counted in errors)

- [ ] **Step 4: Commit**

```bash
git add frontend/e2e/tests/errors.spec.ts
git commit -m "feat: add E2E error display tests"
```

---

## Task 10: CI workflow

**Files:**
- Create: `.github/workflows/playwright-e2e.yml`

- [ ] **Step 1: Create `.github/workflows/playwright-e2e.yml`**

```yaml
name: Playwright E2E Tests

"on":
  pull_request:
    branches:
      - main
    paths:
      - "frontend/**"
      - ".github/workflows/playwright-e2e.yml"
  push:
    branches:
      - main
    paths:
      - "frontend/**"

permissions:
  contents: read

jobs:
  e2e:
    name: Run Playwright E2E
    runs-on: ubuntu-latest
    timeout-minutes: 20
    defaults:
      run:
        working-directory: frontend

    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 # v6.0.3

      - uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020 # v4.4.0
        with:
          node-version: "20"

      - name: Install pnpm
        run: npm install -g pnpm

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Install Playwright browsers
        run: pnpm exec playwright install --with-deps chromium

      - name: Build Next.js
        run: pnpm build
        env:
          SESSION_SECRET: ${{ secrets.E2E_SESSION_SECRET }}
          BACKEND_URL: http://localhost:3001
          SENTRY_UPLOAD_SOURCEMAPS: "false"

      - name: Run Playwright tests
        run: pnpm e2e
        env:
          SESSION_SECRET: ${{ secrets.E2E_SESSION_SECRET }}
          BACKEND_URL: http://localhost:3001
          CI: "true"

      - name: Upload Playwright report
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4.6.2
        if: always()
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 7
```

- [ ] **Step 2: Add `E2E_SESSION_SECRET` to GitHub repository secrets**

1. Go to the repository on GitHub → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `E2E_SESSION_SECRET`
4. Value: run locally to generate → `openssl rand -hex 32` (copy the output)
5. Save

- [ ] **Step 3: Commit and push**

```bash
git add .github/workflows/playwright-e2e.yml
git commit -m "feat: add Playwright E2E CI workflow"
git push origin <current-branch>
```

- [ ] **Step 4: Verify CI passes**

Open the GitHub Actions tab and confirm the "Playwright E2E Tests" workflow runs green. Download the `playwright-report` artifact to inspect any failures.

---

## Self-review checklist

**Spec coverage:**
- ✅ "L'utilisateur peut se connecter" → `auth.spec.ts` login valide
- ✅ "L'utilisateur peut voir la liste de ses discussions passées" → `chat.spec.ts` liste
- ✅ "L'utilisateur peut démarrer une nouvelle discussion" → `chat.spec.ts` nouveau chat
- ✅ "L'utilisateur peut reprendre une ancienne discussion" → `chat.spec.ts` reprendre
- ✅ "Un utilisateur n'est pas autorisé à accéder aux discussions d'un autre" → `isolation.spec.ts`
- ✅ "Le LLM répond aux messages" → `chat.spec.ts` réponse LLM
- ✅ "L'utilisateur peut générer une revue de presse" → `review.spec.ts`
- ✅ "Messages d'erreur en cas d'erreur" → `errors.spec.ts`
- ✅ CI/CD avec mock data → Express mock server + `playwright-e2e.yml`

**Route corrections vs initial spec:**
- Mock uses `POST /chats/message` (not `/chats`) — matches `chat.dal.ts:59`
- Mock uses `POST /chats/:id/review` (not `/reviews/generate/:chatId`) — matches `review.dal.ts:58`
- Mock uses `GET /reviews/chats` (not `/chats/:id/reviews`) — matches `review.dal.ts:72`
- Messages use `type: "ai"` (not `"assistant"`) — matches `AssistantCard.tsx:37`
