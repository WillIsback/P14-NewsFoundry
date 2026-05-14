"use server";
import { getReviews, postCreateReview } from "@/src/service/review.dal";

export type ReviewActionState = {
	error: string | null;
	data?: unknown;
};

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
