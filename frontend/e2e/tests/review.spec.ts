import { expect, test } from "@playwright/test";

test("onglet revues : affiche la liste des revues", async ({ page }) => {
	await page.goto("/home?mode=review");
	// PressReview renders <h4>{title}</h4> — "Revue du jour" from reviewsResponse
	await expect(page.getByText("Revue du jour")).toBeVisible();
});

test("générer une revue depuis un chat : redirige vers /home?mode=review et affiche la revue", async ({
	page,
}) => {
	await page.goto("/chat/1");
	await page
		.getByRole("button", { name: "Générer une revue de presse" })
		.click();
	// ButtonReview opens an inline form — confirm generation without subject
	await page.getByRole("button", { name: "Générer" }).click();
	// ButtonReview pushes /home?mode=review#review-{id} after generation
	await page.waitForURL(/\/home\?mode=review/);
	// "Revue mockée" is id=2 in generateReviewResponse and reviewsResponse fixture
	await expect(
		page.getByRole("heading", { name: "Revue mockée" }),
	).toBeVisible();
});
