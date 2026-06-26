"use client";

import { useEffect, useState } from "react";
import { fetchUserUsage } from "@/src/actions/auth.action";

type Usage = {
	expires_at: string | null;
	worldnews_calls_used: number;
	worldnews_calls_limit: number | null;
	llm_tokens_in_used: number;
	llm_tokens_out_used: number;
	llm_tokens_limit: number | null;
};

export function DemoAccountBanner() {
	const [usage, setUsage] = useState<Usage | null>(null);

	useEffect(() => {
		fetchUserUsage()
			.then((data) => {
				if (data) setUsage(data);
			})
			.catch(() => {});
	}, []);

	if (!usage || usage.expires_at === null) return null;

	const expiresDate = new Date(usage.expires_at).toLocaleDateString("fr-FR", {
		day: "numeric",
		month: "long",
		year: "numeric",
	});

	const llmTotal = usage.llm_tokens_in_used + usage.llm_tokens_out_used;
	const llmLimit = usage.llm_tokens_limit ?? 0;

	return (
		<div className="fixed bottom-4 right-4 z-50 max-w-xs rounded-lg border border-yellow-400 bg-yellow-50 p-3 text-sm shadow-md">
			<p className="font-semibold text-yellow-800">
				⚠️ Compte démo — Expire le {expiresDate}
			</p>
			{usage.worldnews_calls_limit !== null && (
				<p className="mt-1 text-yellow-700">
					WorldNewsAPI : {usage.worldnews_calls_used} /{" "}
					{usage.worldnews_calls_limit} appels
				</p>
			)}
			{usage.llm_tokens_limit !== null && (
				<p className="mt-1 text-yellow-700">
					Tokens LLM : {llmTotal.toLocaleString("fr-FR")} /{" "}
					{llmLimit.toLocaleString("fr-FR")}
				</p>
			)}
		</div>
	);
}
