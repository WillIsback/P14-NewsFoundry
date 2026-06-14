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
