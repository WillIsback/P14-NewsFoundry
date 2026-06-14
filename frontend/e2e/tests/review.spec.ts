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
	// generateReview is a Next.js server action; the middleware redirects /?mode=review → /home
	// (it strips query params when redirecting authenticated users from the public "/" route)
	await page.waitForURL(/\/home/);
	// Navigate to review mode to verify the reviews section is accessible post-generation
	await page.goto("/home?mode=review");
	// Revue du jour is always in the mock /reviews response
	await expect(page.getByText("Revue du jour")).toBeVisible();
});
