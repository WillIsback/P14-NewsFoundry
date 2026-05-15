import "server-only";
import type { z } from "zod/v4";
import { fetchJson } from "@/src/lib/fetch.lib";
import { getBearerToken } from "@/src/lib/session";
import type { ServiceResult } from "@/src/lib/type.lib";
import {
	chatContinueChatMessage200Schema,
	chatContinueChatMessage422Schema,
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
type NewChatMessageResponse = z.infer<typeof chatNewChatMessage201Schema>;
type ContinueChatMessageResponse = z.infer<
	typeof chatContinueChatMessage200Schema
>;

async function authHeaders(): Promise<HeadersInit> {
	const token = await getBearerToken();
	return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getChats(): Promise<ServiceResult<GetChatsResponse>> {
	return fetchJson({
		url: `${BACKEND_URL}/chats`,
		method: "GET",
		successSchema: chatGetChats200Schema,
		headers: await authHeaders(),
		fetchOptions: { cache: "no-store" },
	});
}

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
		fetchOptions: { cache: "no-store" },
	});
}

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
		fetchOptions: { cache: "no-store" },
	});
}
