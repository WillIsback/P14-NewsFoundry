"use client";

import { use, useEffect } from "react";
import PressReview from "./PressReview";

interface ReviewItem {
	id: number;
	title: string;
	description: string;
	content: string;
	date?: string;
}

export default function DisplayReviews({
	reviewsPromise,
	chatReviewsPromise,
}: Readonly<{
	reviewsPromise: Promise<ReviewItem[]>;
	chatReviewsPromise: Promise<ReviewItem[]>;
}>) {
	const reviews = use(reviewsPromise);
	const chatReviews = use(chatReviewsPromise);
	const allReviews = [...reviews, ...chatReviews];

	useEffect(() => {
		if (window.location.hash) {
			const el = document.getElementById(window.location.hash.slice(1));
			el?.scrollIntoView({ behavior: "smooth", block: "start" });
		}
	}, []);

	return (
		<div className="flex flex-col h-full min-h-0">
			<header className="flex flex-col h-fit w-full shrink-0">
				<h1 className="text-2xl font-bold">Revues de Presse</h1>
				<p className="text-slate-600">
					Consultez vos revues de presse générées par l&apos;IA
				</p>
			</header>
			<div className="flex-1 overflow-y-auto flex flex-col gap-4 mt-4">
				{allReviews.length === 0 && (
					<p className="text-slate-800 text-center">
						Aucune revue de presse pour le moment. Générez-en une depuis une
						discussion !
					</p>
				)}
				{allReviews.map((review) => (
					<PressReview key={review.id} {...review} />
				))}
			</div>
		</div>
	);
}
