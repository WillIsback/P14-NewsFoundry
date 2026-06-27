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

/**
 * Server action state shared by review actions.
 */
export type ReviewActionState = {
	error: string | null;
	data?: unknown;
};

type ChatGenerateReviewResponse = z.infer<
	typeof chatGenerateChatReview201Schema
>;

/**
 * Fetches all saved reviews for the current user.
 *
 * @returns An object with either the reviews list or an error message.
 */
export async function fetchReviews() {
	const result = await getReviews();
	if (!result.ok) {
		return { error: result.error.userMessage, data: null };
	}
	return { error: null, data: result.data };
}

/**
 * Server action to create a new review for provided articles.
 *
 * @param _initialState - The previous action state (ignored in initial calls).
 * @param formData - Form data containing the `articles` field with the articles to review.
 * @returns The action state with error or the generated review.
 */
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

/**
 * Server action to generate a review for articles discussed in a chat.
 *
 * @param chatId - The ID of the chat to generate a review from.
 * @param articleUrl - Optional URL of a specific article to focus the review on.
 * @returns An object with error or the generated review.
 */
export async function generateReview(
	chatId: number,
	articleUrl?: string,
): Promise<{ error: string | null; data: ChatGenerateReviewResponse | null }> {
	const result = await postGenerateReview(chatId, articleUrl);
	if (!result.ok) {
		return { error: result.error.userMessage, data: null };
	}
	revalidatePath("/");
	return { error: null, data: result.data };
}

/**
 * Fetches all reviews generated from chat conversations for the current user.
 *
 * @returns An object with either the chat reviews list or an error message.
 */
export async function fetchChatReviews() {
	const result = await getChatReviews();
	if (!result.ok) {
		return { error: result.error.userMessage, data: null };
	}
	return { error: null, data: result.data };
}
