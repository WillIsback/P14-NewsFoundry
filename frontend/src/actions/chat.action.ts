"use server";
import {
	getChats,
	getMessages,
	postContinueChatMessage,
	postNewChatMessage,
} from "@/src/service/chat.dal";

export type ChatActionState = {
	error: string | null;
};

export async function fetchChats() {
	const result = await getChats();
	if (!result.ok) {
		return { error: result.error.userMessage, data: null };
	}
	return { error: null, data: result.data };
}

export async function fetchMessages(chatId: number) {
	const result = await getMessages(chatId);
	if (!result.ok) {
		return { error: result.error.userMessage, data: null };
	}
	return { error: null, data: result.data };
}

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
	return { error: null, data: result.data };
}

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
	return { error: null, data: result.data };
}
