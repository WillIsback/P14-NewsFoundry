"use server";

import { revalidatePath } from "next/cache";
import type { z } from "zod/v4";
import type { chatGenerateChatReview201Schema } from "@/src/models/gen";
import {
	getChatReviews,
	getReviews,
	postCreateReview,
	postGenerateReview,
} from "@/src/service/review.dal";

export type ReviewActionState = {
	error: string | null;
	data?: unknown;
};

type ChatGenerateReviewResponse = z.infer<
	typeof chatGenerateChatReview201Schema
>;

export async function fetchReviews() {
	const result = await getReviews();
	if (!result.ok) {
		return { error: result.error.userMessage, data: null };
	}
	return { error: null, data: result.data };
}

export async function createReview(
	_initialState: ReviewActionState,
	formData: FormData,
): Promise<ReviewActionState> {
	const articles = formData.get("articles");
	if (typeof articles !== "string" || articles.trim().length === 0) {
		return { error: "Le contenu des articles ne peut pas être vide" };
	}

	const result = await postCreateReview(articles.trim());
	if (!result.ok) {
		return { error: result.error.userMessage };
	}
	return { error: null, data: result.data };
}

export async function generateReview(
	chatId: number,
	subject?: string,
): Promise<{ error: string | null; data: ChatGenerateReviewResponse | null }> {
	const result = await postGenerateReview(chatId, subject);
	if (!result.ok) {
		return { error: result.error.userMessage, data: null };
	}
	revalidatePath("/");
	return { error: null, data: result.data };
}

export async function fetchChatReviews() {
	const result = await getChatReviews();
	if (!result.ok) {
		return { error: result.error.userMessage, data: null };
	}
	return { error: null, data: result.data };
}
