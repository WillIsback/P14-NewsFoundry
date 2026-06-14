import { expect, test } from "@playwright/test";
import { USER_B_STATE } from "../fixtures/auth.js";

test.use({ storageState: USER_B_STATE });

test("user-b ne voit que ses propres chats", async ({ page }) => {
	await page.goto("/home");
	// chatsUserB fixture has only id=3, date "12/01/2024"
	const links = page.getByRole("link", { name: /Discussion du/ });
	await expect(links).toHaveCount(1);
	await expect(page.getByRole("link", { name: /12\/01\/2024/ })).toBeVisible();
	// user-a's chats (15/01/2024 and 10/01/2024) must not appear
	await expect(
		page.getByRole("link", { name: /15\/01\/2024/ }),
	).not.toBeVisible();
});

test("user-b ne peut pas accéder au chat de user-a (/chat/1 → 404)", async ({
	page,
}) => {
	await page.goto("/chat/1");
	// fetchMessages(1) returns 404 for user-b → Next.js calls notFound()
	// not-found.tsx renders "Conversation introuvable"
	await expect(
		page.getByRole("heading", { name: "Conversation introuvable" }),
	).toBeVisible();
});
