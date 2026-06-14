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

async function authHeaders(): Promise<HeadersInit> {
	const token = await getBearerToken();
	return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getReviews(): Promise<ServiceResult<GetReviewsResponse>> {
	return fetchJson({
		url: `${BACKEND_URL}/reviews`,
		method: "GET",
		successSchema: reviewGetReviews200Schema,
		headers: await authHeaders(),
		fetchOptions: { cache: "no-store" },
	});
}

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

export async function postGenerateReview(
	chatId: number,
): Promise<ServiceResult<ChatReviewGenerateResponse>> {
	return fetchJson({
		url: `${BACKEND_URL}/chats/${chatId}/review`,
		method: "POST",
		successSchema: chatGenerateChatReview201Schema,
		headers: await authHeaders(),
		timeoutMs: 60_000,
		fetchOptions: { cache: "no-store" },
	});
}

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
