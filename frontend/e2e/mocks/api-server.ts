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
	TOKEN_ERROR,
	TOKEN_USER_A,
	TOKEN_USER_B,
	USER_A_EMAIL,
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

// /chats/message creates a new chat; POST /chats is the list endpoint
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
	res.json(continueChatResponse);
});

// review generation lives under the chat resource, not under /reviews
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

// chat reviews are fetched from /reviews/chats (not per-chat sub-resource)
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
