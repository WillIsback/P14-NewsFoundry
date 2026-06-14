import { expect, test } from "@playwright/test";
import { NO_AUTH_STATE, USER_A_STATE } from "../fixtures/auth.js";

test.describe("unauthenticated", () => {
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
});

test.describe("authenticated", () => {
	test.use({ storageState: USER_A_STATE });

	test("déconnexion : redirige vers /login", async ({ page }) => {
		await page.goto("/home");
		await page.getByRole("button", { name: "Se deconnecter" }).click();
		await expect(page).toHaveURL("/login");
	});
});
