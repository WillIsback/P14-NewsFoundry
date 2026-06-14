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
		// user-error token → mock returns 500 on all endpoints → ErrorBoundary renders
		await expect(
			page.getByText("Impossible de charger les revues de presse."),
		).toBeVisible();
	});
});
