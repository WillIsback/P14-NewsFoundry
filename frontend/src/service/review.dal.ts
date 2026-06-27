import "server-only";
import type { z } from "zod/v4";
import { fetchJson } from "@/src/lib/fetch.lib";
import { getBearerToken } from "@/src/lib/session";
import type { ServiceResult } from "@/src/lib/type.lib";
import {
	chatGenerateChatReview201Schema,
	reviewCreateReview201Schema,
	reviewCreateReview422Schema,
	reviewGetChatReviews200Schema,
	reviewGetReviews200Schema,
} from "@/src/models/gen";

const BACKEND_URL = (
	process.env.BACKEND_URL || "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

type GetReviewsResponse = z.infer<typeof reviewGetReviews200Schema>;
type CreateReviewResponse = z.infer<typeof reviewCreateReview201Schema>;
type ChatReviewGenerateResponse = z.infer<
	typeof chatGenerateChatReview201Schema
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
 * Fetches all saved reviews for the authenticated user.
 *
 * @returns A ServiceResult containing the list of reviews or an error.
 *
 * @example
 * ```typescript
 * const result = await getReviews();
 * if (result.ok) {
 *   const reviews = result.data.data;
 *   reviews.forEach(review => console.log(review.title));
 * }
 * ```
 */
export async function getReviews(): Promise<ServiceResult<GetReviewsResponse>> {
	return fetchJson({
		url: `${BACKEND_URL}/reviews`,
		method: "GET",
		successSchema: reviewGetReviews200Schema,
		headers: await authHeaders(),
		fetchOptions: { cache: "no-store" },
	});
}

/**
 * Creates a new review for the provided articles.
 *
 * The LLM generates a structured critique with analysis, pros, cons, and rating.
 *
 * @param articles - A string containing the articles to review (typically in JSON format).
 * @returns A ServiceResult containing the generated review or an error.
 *
 * @example
 * ```typescript
 * const articleJson = JSON.stringify([{ title: "Article 1", body: "..." }]);
 * const result = await postCreateReview(articleJson);
 * if (result.ok) {
 *   console.log(result.data.data.review.analysis);
 * }
 * ```
 */
export async function postCreateReview(
	articles: string,
): Promise<ServiceResult<CreateReviewResponse>> {
	return fetchJson({
		url: `${BACKEND_URL}/reviews`,
		method: "POST",
		requestData: { articles },
		successSchema: reviewCreateReview201Schema,
		errorSchemas: { 422: reviewCreateReview422Schema },
		headers: await authHeaders(),
		timeoutMs: 60_000,
		fetchOptions: { cache: "no-store" },
	});
}

/**
 * Generates a review for articles discussed in a chat conversation.
 *
 * Optionally can focus on a specific article URL if provided.
 *
 * @param chatId - The ID of the chat containing the articles to review.
 * @param articleUrl - Optional URL of a specific article to focus the review on.
 * @returns A ServiceResult containing the generated review or an error.
 *
 * @example
 * ```typescript
 * const result = await postGenerateReview(123);
 * if (result.ok) {
 *   const review = result.data.data;
 *   console.log(review.review.analysis);
 * }
 * ```
 */
export async function postGenerateReview(
	chatId: number,
	articleUrl?: string,
): Promise<ServiceResult<ChatReviewGenerateResponse>> {
	return fetchJson({
		url: `${BACKEND_URL}/chats/${chatId}/review`,
		method: "POST",
		requestData: articleUrl ? { article_url: articleUrl } : undefined,
		successSchema: chatGenerateChatReview201Schema,
		headers: await authHeaders(),
		timeoutMs: 60_000,
		fetchOptions: { cache: "no-store" },
	});
}

/**
 * Fetches all reviews generated from chat conversations for the authenticated user.
 *
 * @returns A ServiceResult containing the list of chat-based reviews or an error.
 */
export async function getChatReviews(): Promise<
	ServiceResult<GetReviewsResponse>
> {
	return fetchJson({
		url: `${BACKEND_URL}/reviews/chats`,
		method: "GET",
		successSchema: reviewGetChatReviews200Schema,
		headers: await authHeaders(),
		fetchOptions: { cache: "no-store" },
	});
}
