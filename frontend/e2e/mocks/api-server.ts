import express from "express";
import {
	chatReviewsResponse,
	chatsUserA,
	chatsUserB,
	continueChatResponse,
	generateReviewResponse,
	loginOkResponse,
	messagesChat1,
	newChatResponse,
	PASSWORD_OK,
	reviewsResponse,
	TOKEN_CHATS_500,
	TOKEN_CHATS_TIMEOUT,
	TOKEN_CONTINUE_500,
	TOKEN_ERROR,
	TOKEN_GENERATE_REVIEW_500,
	TOKEN_NEWCHAT_500,
	TOKEN_NEWCHAT_TIMEOUT,
	TOKEN_RATE_LIMITED_CHATS,
	TOKEN_RATE_LIMITED_POST,
	TOKEN_SESSION_EXPIRED,
	TOKEN_USER_B,
	USER_A_EMAIL,
} from "../fixtures/data.js";

// Délai en ms que le mock attend avant de répondre pour les tokens *_TIMEOUT.
// Doit être supérieur à FETCH_DEFAULT_TIMEOUT_MS et FETCH_CHAT_TIMEOUT_MS définis dans playwright.config.ts.
const MOCK_SLOW_DELAY_MS = Number(process.env.MOCK_SLOW_DELAY_MS ?? 700);

function delay(ms: number): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

const app = express();
app.use(express.json());

function extractToken(req: express.Request): string | null {
	const auth = req.headers.authorization;
	if (!auth?.startsWith("Bearer ")) return null;
	return auth.slice(7);
}

/**
 * Vérifie l'auth et les tokens globaux (TOKEN_ERROR, TOKEN_SESSION_EXPIRED).
 * Retourne le token si valide, null si la réponse d'erreur a déjà été envoyée.
 */
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
	if (token === TOKEN_SESSION_EXPIRED) {
		res.status(401).json({ detail: "Session expired" });
		return null;
	}
	return token;
}

// POST /auth/login
app.post("/auth/login", (req, res) => {
	const body = req.body as Record<string, unknown>;
	const email = typeof body?.email === "string" ? body.email : undefined;
	const password =
		typeof body?.password === "string" ? body.password : undefined;
	if (email === USER_A_EMAIL && password === PASSWORD_OK) {
		res.json(loginOkResponse);
	} else {
		res.status(422).json({ detail: [] });
	}
});

// GET /chats
app.get("/chats", async (req, res) => {
	const token = requireAuth(req, res);
	if (!token) return;
	if (token === TOKEN_CHATS_500) {
		res.status(500).json({ detail: "Internal server error" });
		return;
	}
	if (token === TOKEN_CHATS_TIMEOUT) {
		await delay(MOCK_SLOW_DELAY_MS);
		res.json(chatsUserA);
		return;
	}
	if (token === TOKEN_RATE_LIMITED_CHATS) {
		res.status(429).json({ detail: "Too Many Requests" });
		return;
	}
	if (token === TOKEN_USER_B) {
		res.json(chatsUserB);
	} else {
		// TOKEN_USER_A et tous les tokens d'erreur par endpoint reçoivent user-a
		res.json(chatsUserA);
	}
});

// POST /chats/message — crée un nouveau chat
app.post("/chats/message", async (req, res) => {
	const token = requireAuth(req, res);
	if (!token) return;
	if (token === TOKEN_NEWCHAT_500) {
		res.status(500).json({ detail: "Internal server error" });
		return;
	}
	if (token === TOKEN_NEWCHAT_TIMEOUT) {
		await delay(MOCK_SLOW_DELAY_MS);
		res.status(201).json(newChatResponse);
		return;
	}
	if (token === TOKEN_RATE_LIMITED_POST) {
		res.status(429).json({ detail: "Too Many Requests" });
		return;
	}
	res.status(201).json(newChatResponse);
});

// GET /chats/:chatId/messages
app.get("/chats/:chatId/messages", (req, res) => {
	const token = requireAuth(req, res);
	if (!token) return;
	const chatId = Number(req.params.chatId);
	if (Number.isNaN(chatId)) {
		res.status(400).json({ detail: "Invalid chat ID" });
		return;
	}
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
	if (token === TOKEN_CONTINUE_500) {
		res.status(500).json({ detail: "Internal server error" });
		return;
	}
	res.json(continueChatResponse);
});

// POST /chats/:chatId/review — génération revue
app.post("/chats/:chatId/review", (req, res) => {
	const token = requireAuth(req, res);
	if (!token) return;
	if (token === TOKEN_GENERATE_REVIEW_500) {
		res.status(500).json({ detail: "Internal server error" });
		return;
	}
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

const server = app.listen(3001, "127.0.0.1", () => {
	console.log("[mock-api] Server running on http://localhost:3001");
});

process.on("SIGTERM", () => server.close(() => process.exit(0)));
process.on("SIGINT", () => server.close(() => process.exit(0)));
