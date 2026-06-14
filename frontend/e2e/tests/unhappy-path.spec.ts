import { expect, test as base } from "@playwright/test";
import {
	CHATS_500_STATE,
	CONTINUE_500_STATE,
	GENERATE_REVIEW_500_STATE,
	NEWCHAT_500_STATE,
	NO_AUTH_STATE,
	SESSION_EXPIRED_STATE,
	USER_ERROR_STATE,
} from "../fixtures/auth.js";

// Fixture qui capture les erreurs/warnings console côté browser et les attache au rapport HTML.
const test = base.extend<{ consoleLogs: string[] }>({
	consoleLogs: async ({ page }, use, testInfo) => {
		const logs: string[] = [];
		page.on("console", (msg) => {
			if (msg.type() === "error" || msg.type() === "warning") {
				logs.push(`[${msg.type()}] ${msg.text()}`);
			}
		});
		page.on("pageerror", (err) => {
			logs.push(`[pageerror] ${err.message}`);
		});
		await use(logs);
		if (logs.length > 0) {
			await testInfo.attach("console-logs", {
				body: logs.join("\n"),
				contentType: "text/plain",
			});
		}
	},
});

async function attachScreenshot(page: { screenshot(): Promise<Buffer> }, name: string) {
	const screenshot = await page.screenshot();
	await test.info().attach(name, { body: screenshot, contentType: "image/png" });
}

// ─── 1. Login — champs vides ─────────────────────────────────────────────────

test.describe("login — champs vides", () => {
	test.use({ storageState: NO_AUTH_STATE });

	test("soumettre sans remplir : validation HTML5 bloque la navigation", async ({
		page,
		consoleLogs: _,
	}) => {
		await page.goto("/login");
		await page.getByRole("button", { name: "Se connecter" }).click();
		// HTML5 required bloque l'action — on reste sur /login
		await expect(page).toHaveURL("/login");
		await attachScreenshot(page, "login-champs-vides");
	});
});

// ─── 2. Login — credentials invalides ────────────────────────────────────────

test.describe("login — credentials invalides", () => {
	test.use({ storageState: NO_AUTH_STATE });

	test("mauvais mot de passe : role=status avec message d'erreur", async ({
		page,
		consoleLogs: _,
	}) => {
		await page.goto("/login");
		await page.getByLabel("Adresse email").fill("user-a@test.com");
		await page.getByLabel("Mot de passe").fill("wrong-password");
		await page.getByRole("button", { name: "Se connecter" }).click();
		await expect(page.getByRole("status")).toBeVisible();
		await expect(page.getByRole("status")).toContainText(
			"Le formulaire de connexion est invalide",
		);
		await attachScreenshot(page, "login-mauvais-mdp");
	});
});

// ─── 3. Session expirée ───────────────────────────────────────────────────────

test.describe("session expirée", () => {
	test.use({ storageState: SESSION_EXPIRED_STATE });

	test("token backend expiré sur /chat/1 : page not-found (redirect non propagé)", async ({
		page,
		consoleLogs: _,
	}) => {
		// Comportement observé : fetchJson reçoit 401, appelle deleteSession() + redirect().
		// NEXT_REDIRECT n'est pas propagé hors de fetchJson (unstable_rethrow limité en prod).
		// fetchMessages retourne { error } → notFound() → page 404.
		// NOTE : l'utilisateur voit une page 404 au lieu d'être redirigé vers /login.
		// C'est une limitation documentée — la redirection 401 ne fonctionne que si le
		// fetch est directement awaité dans un Server Action appelé depuis un Server Component
		// sans passer par le catch block de fetchJson.
		await page.goto("/chat/1");
		await expect(
			page.getByRole("heading", { name: "Conversation introuvable" }),
		).toBeVisible();
		await attachScreenshot(page, "session-token-expire-404");
	});
});

// ─── 4. Sidebar — GET /chats 500 ─────────────────────────────────────────────

test.describe("sidebar — GET /chats 500", () => {
	test.use({ storageState: CHATS_500_STATE });

	test("erreur 500 sur /chats : message d'erreur sidebar visible", async ({
		page,
		consoleLogs: _,
	}) => {
		await page.goto("/home");
		// ErrorBoundary de la sidebar affiche le fallback visible (bug corrigé)
		await expect(
			page.getByText("Impossible de charger les discussions."),
		).toBeVisible();
		await attachScreenshot(page, "sidebar-chats-500");
	});
});

// ─── 5. Page chat — messages introuvables (404) ───────────────────────────────

test.describe("page chat — messages 404", () => {
	// storageState par défaut = user-a (configuré dans playwright.config.ts)

	test("accès à /chat/999 : page not-found avec heading", async ({
		page,
		consoleLogs: _,
	}) => {
		await page.goto("/chat/999");
		// fetchMessages(999) → 404 → notFound() → not-found.tsx
		await expect(
			page.getByRole("heading", { name: "Conversation introuvable" }),
		).toBeVisible();
		await attachScreenshot(page, "chat-messages-404");
	});
});

// ─── 6. ChatForm — envoi message vide ────────────────────────────────────────

test.describe("chatform — envoi message vide", () => {
	// storageState par défaut = user-a

	test("soumettre textarea vide : alerte accessible (sr-only)", async ({
		page,
		consoleLogs: _,
	}) => {
		await page.goto("/home");
		// Soumettre sans remplir le textarea (pas d'attribut required sur TextArea)
		await page.getByRole("button", { name: /envoyer/i }).click();
		// L'action retourne { error: "Le message ne peut pas être vide" }
		// Rendu dans <p role="alert" className="sr-only"> — accessible mais non visuel.
		// NOTE UX : cette erreur est invisible pour les utilisateurs voyants.
		// Elle devrait être visible (retirer sr-only ou dupliquer en visible).
		// Cibler p[role="alert"] pour éviter le conflit avec le route-announcer de Next.js.
		const alert = page.locator('p[role="alert"]');
		await expect(alert).toBeAttached();
		await expect(alert).toContainText("Le message ne peut pas être vide");
		await attachScreenshot(page, "chatform-message-vide");
	});
});

// ─── 7. ChatForm — POST new chat 500 ─────────────────────────────────────────

test.describe("chatform — POST /chats/message 500", () => {
	test.use({ storageState: NEWCHAT_500_STATE });

	test("nouveau chat 500 : alerte accessible avec message d'erreur serveur", async ({
		page,
		consoleLogs: _,
	}) => {
		await page.goto("/home");
		await page.getByLabel("Message").fill("Question de test");
		await page.getByRole("button", { name: /envoyer/i }).click();
		// userMessage issu de fetch.lib.ts pour HTTP 500 : "La requete a echoue"
		const alertNew = page.locator('p[role="alert"]');
		await expect(alertNew).toBeAttached();
		await expect(alertNew).toContainText("La requete a echoue");
		await attachScreenshot(page, "chatform-newchat-500");
	});
});

// ─── 8. ChatForm — POST continue chat 500 ────────────────────────────────────

test.describe("chatform — POST /chats/:id/messages 500", () => {
	test.use({ storageState: CONTINUE_500_STATE });

	test("continuer chat 500 : alerte accessible avec message d'erreur serveur", async ({
		page,
		consoleLogs: _,
	}) => {
		await page.goto("/chat/1");
		await page.getByLabel("Message").fill("Message de suivi");
		await page.getByRole("button", { name: /envoyer/i }).click();
		const alertContinue = page.locator('p[role="alert"]');
		await expect(alertContinue).toBeAttached();
		await expect(alertContinue).toContainText("La requete a echoue");
		await attachScreenshot(page, "chatform-continue-500");
	});
});

// ─── 9. ButtonReview — POST /chats/:id/review 500 ────────────────────────────

test.describe("ButtonReview — POST generate review 500", () => {
	test.use({ storageState: GENERATE_REVIEW_500_STATE });

	test("générer revue 500 : message d'erreur visible sous le bouton", async ({
		page,
		consoleLogs: _,
	}) => {
		await page.goto("/chat/1");
		await page
			.getByRole("button", { name: "Générer une revue de presse" })
			.click();
		// generateReview() retourne { error: result.error.userMessage } → setError("La requete a echoue")
		// ButtonReview rend <p className="text-red-500">{error}</p> — visible pour l'utilisateur
		await expect(page.getByText("La requete a echoue")).toBeVisible();
		await attachScreenshot(page, "buttonreview-generate-500");
	});
});

// ─── 10. Reviews ErrorBoundary — GET /reviews 500 ────────────────────────────

test.describe("reviews — GET /reviews 500", () => {
	test.use({ storageState: USER_ERROR_STATE });

	test("reviews 500 : ErrorBoundary affiche le fallback visible", async ({
		page,
		consoleLogs: _,
	}) => {
		await page.goto("/home?mode=review");
		await expect(
			page.getByText("Impossible de charger les revues de presse."),
		).toBeVisible();
		await attachScreenshot(page, "reviews-500-errorboundary");
	});
});
