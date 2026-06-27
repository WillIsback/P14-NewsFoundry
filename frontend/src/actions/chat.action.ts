"use server";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import {
	getChatArticles,
	getChats,
	getMessages,
	postContinueChatMessage,
	postNewChatMessage,
} from "@/src/service/chat.dal";

/**
 * Server action state shared by chat actions.
 */
export type ChatActionState = {
	error: string | null;
};

/**
 * Fetches the list of chats for the current user.
 *
 * @returns An object with either the chat list or an error message.
 */
export async function fetchChats() {
	const result = await getChats();
	if (!result.ok) {
		return { error: result.error.userMessage, data: null };
	}
	return { error: null, data: result.data };
}

/**
 * Fetches the source articles for a specific chat.
 *
 * @param chatId - The ID of the chat to fetch articles for.
 * @returns An object with either the articles list or an error message.
 */
export async function fetchChatArticles(chatId: number) {
	const result = await getChatArticles(chatId);
	if (!result.ok) {
		return {
			error:
				result.error?.userMessage ?? "Erreur lors du chargement des articles",
			data: [] as { title: string; url: string }[],
		};
	}
	return { error: null, data: result.data?.data ?? [] };
}

/**
 * Fetches the messages for a specific chat.
 *
 * @param chatId - The ID of the chat to fetch messages for.
 * @returns An object with either the messages or an error message.
 */
export async function fetchMessages(chatId: number) {
	const result = await getMessages(chatId);
	if (!result.ok) {
		return { error: result.error.userMessage, data: null };
	}
	return { error: null, data: result.data };
}

/**
 * Server action to send a new message and start a chat.
 *
 * Validates the message content, sends it to the backend, and redirects to the new chat page.
 *
 * @param _initialState - The previous action state (ignored in initial calls).
 * @param formData - Form data containing the `content` field with the message text.
 * @returns The action state with error or success, or redirects on successful chat creation.
 */
export async function sendNewMessage(
	_initialState: ChatActionState,
	formData: FormData,
): Promise<ChatActionState & { data?: unknown }> {
	const content = formData.get("content");
	if (typeof content !== "string" || content.trim().length === 0) {
		return { error: "Le message ne peut pas être vide" };
	}

	const result = await postNewChatMessage(content.trim());
	if (!result.ok) {
		return { error: result.error.userMessage };
	}
	const chatId = result.data.data?.chat_id;
	if (!chatId) {
		return { error: "Erreur lors de la création du chat" };
	}
	redirect(`/chat/${chatId}`);
}

/**
 * Server action to send a follow-up message in an existing chat.
 *
 * Validates the message content, sends it to the backend, and revalidates the chat page.
 *
 * @param chatId - The ID of the chat to continue.
 * @param _initialState - The previous action state (ignored in initial calls).
 * @param formData - Form data containing the `content` field with the message text.
 * @returns The action state with error or success message.
 */
export async function continueChat(
	chatId: number,
	_initialState: ChatActionState,
	formData: FormData,
): Promise<ChatActionState & { data?: unknown }> {
	const content = formData.get("content");
	if (typeof content !== "string" || content.trim().length === 0) {
		return { error: "Le message ne peut pas être vide" };
	}

	const result = await postContinueChatMessage(chatId, content.trim());
	if (!result.ok) {
		return { error: result.error.userMessage };
	}
	revalidatePath(`/chat/${chatId}`);
	return { error: null, data: result.data };
}
