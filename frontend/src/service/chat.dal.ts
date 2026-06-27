import "server-only";
import type { z } from "zod/v4";
import { fetchJson } from "@/src/lib/fetch.lib";
import { getBearerToken } from "@/src/lib/session";
import type { ServiceResult } from "@/src/lib/type.lib";
import {
	chatContinueChatMessage200Schema,
	chatContinueChatMessage422Schema,
	chatGetChatArticles200Schema,
	chatGetChats200Schema,
	chatGetMessages200Schema,
	chatGetMessages422Schema,
	chatNewChatMessage201Schema,
	chatNewChatMessage422Schema,
} from "@/src/models/gen";

const BACKEND_URL = (
	process.env.BACKEND_URL || "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

type GetChatsResponse = z.infer<typeof chatGetChats200Schema>;
type GetMessagesResponse = z.infer<typeof chatGetMessages200Schema>;
type GetChatArticlesResponse = z.infer<typeof chatGetChatArticles200Schema>;
type NewChatMessageResponse = z.infer<typeof chatNewChatMessage201Schema>;
type ContinueChatMessageResponse = z.infer<
	typeof chatContinueChatMessage200Schema
>;

/**
 * Builds authorization headers with the Bearer token from the current session.
 *
 * @returns An object with the Authorization header if a token exists, otherwise an empty object.
 */
async function authHeaders(): Promise<HeadersInit> {
	const token = await getBearerToken();
	return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Fetches the list of chats for the authenticated user.
 *
 * @returns A ServiceResult containing the list of chats or an error.
 *
 * @example
 * ```typescript
 * const result = await getChats();
 * if (result.ok) {
 *   const chats = result.data.data;
 *   chats.forEach(chat => console.log(chat.title));
 * }
 * ```
 */
export async function getChats(): Promise<ServiceResult<GetChatsResponse>> {
	return fetchJson({
		url: `${BACKEND_URL}/chats`,
		method: "GET",
		successSchema: chatGetChats200Schema,
		headers: await authHeaders(),
		fetchOptions: { cache: "no-store" },
	});
}

/**
 * Fetches the messages for a specific chat.
 *
 * @param chatId - The ID of the chat to retrieve messages for.
 * @returns A ServiceResult containing the chat messages or an error.
 *
 * @example
 * ```typescript
 * const result = await getMessages(123);
 * if (result.ok) {
 *   const messages = result.data.data;
 *   messages.forEach(msg => console.log(msg.content));
 * }
 * ```
 */
export async function getMessages(
	chatId: number,
): Promise<ServiceResult<GetMessagesResponse>> {
	return fetchJson({
		url: `${BACKEND_URL}/chats/${chatId}/messages`,
		method: "GET",
		successSchema: chatGetMessages200Schema,
		errorSchemas: { 422: chatGetMessages422Schema },
		headers: await authHeaders(),
		fetchOptions: { cache: "no-store" },
	});
}

/**
 * Sends a new message to start a new chat with the AI assistant.
 *
 * The assistant generates a response using the WorldNews tool and LLM calls.
 * This operation has a longer timeout (120s by default) to accommodate LLM inference.
 *
 * @param content - The message content to send.
 * @returns A ServiceResult containing the assistant's response or an error.
 *
 * @example
 * ```typescript
 * const result = await postNewChatMessage("Tell me about AI news");
 * if (result.ok) {
 *   const chatId = result.data.data.chat_id;
 *   const firstMessage = result.data.data.messages[0];
 * }
 * ```
 */
export async function postNewChatMessage(
	content: string,
): Promise<ServiceResult<NewChatMessageResponse>> {
	return fetchJson({
		url: `${BACKEND_URL}/chats/message`,
		method: "POST",
		requestData: { content },
		successSchema: chatNewChatMessage201Schema,
		errorSchemas: { 422: chatNewChatMessage422Schema },
		headers: await authHeaders(),
		// L'agent (WorldNews + 2 appels LLM) dépasse le défaut de 10s.
		// FETCH_CHAT_TIMEOUT_MS permet aux tests d'abaisser cette valeur sans toucher le code.
		timeoutMs: Number(process.env.FETCH_CHAT_TIMEOUT_MS ?? 120_000),
		fetchOptions: { cache: "no-store" },
	});
}

/**
 * Fetches the source articles used by the assistant for a specific chat.
 *
 * @param chatId - The ID of the chat to retrieve articles for.
 * @returns A ServiceResult containing the articles or an error.
 */
export async function getChatArticles(
	chatId: number,
): Promise<ServiceResult<GetChatArticlesResponse>> {
	return fetchJson({
		url: `${BACKEND_URL}/chats/${chatId}/articles`,
		method: "GET",
		successSchema: chatGetChatArticles200Schema,
		headers: await authHeaders(),
		fetchOptions: { cache: "no-store" },
	});
}

/**
 * Sends a follow-up message to an existing chat conversation.
 *
 * The assistant generates a response using the WorldNews tool and LLM calls.
 * This operation has a longer timeout (120s by default) to accommodate LLM inference.
 *
 * @param chatId - The ID of the chat to continue.
 * @param content - The message content to send.
 * @returns A ServiceResult containing the assistant's response or an error.
 */
export async function postContinueChatMessage(
	chatId: number,
	content: string,
): Promise<ServiceResult<ContinueChatMessageResponse>> {
	return fetchJson({
		url: `${BACKEND_URL}/chats/${chatId}/messages`,
		method: "POST",
		requestData: { content },
		successSchema: chatContinueChatMessage200Schema,
		errorSchemas: { 422: chatContinueChatMessage422Schema },
		headers: await authHeaders(),
		// L'agent (WorldNews + 2 appels LLM) dépasse le défaut de 10s.
		timeoutMs: Number(process.env.FETCH_CHAT_TIMEOUT_MS ?? 120_000),
		fetchOptions: { cache: "no-store" },
	});
}
