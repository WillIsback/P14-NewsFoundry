"use client";

import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { useState } from "react";
import Markdown, { type Components } from "react-markdown";
import { Button } from "@/src/components/ui/button";

const markdownComponents: Components = {
	ul: ({ children }) => (
		<ul className="list-disc list-inside my-2">{children}</ul>
	),
	ol: ({ children }) => (
		<ol className="list-decimal list-inside my-2">{children}</ol>
	),
};

interface PressReviewProps {
	title: string;
	description: string;
	content: string;
}

export default function PressReview({
	title,
	description,
	content,
}: Readonly<PressReviewProps>) {
	const [copied, setCopied] = useState(false);
	const formattedDate = format(
		new Date(description),
		"eeee d MMMM yyyy 'à' HH:mm",
		{ locale: fr },
	);

	let articles: { title: string; summary: string; source?: string }[] | null =
		null;
	try {
		const parsed = JSON.parse(content);
		if (Array.isArray(parsed)) {
			articles = parsed;
		} else if (parsed.articles && Array.isArray(parsed.articles)) {
			articles = parsed.articles;
		}
	} catch {
		// Not JSON — legacy markdown content
	}

	const calIcon = (
		<svg
			width="16"
			height="16"
			viewBox="0 0 16 16"
			fill="none"
			xmlns="http://www.w3.org/2000/svg"
		>
			<title>Date de publication</title>
			<path
				d="M5.3335 1.3335V4.00016"
				stroke="#717182"
				strokeWidth="1.33333"
				strokeLinecap="round"
				strokeLinejoin="round"
			/>
			<path
				d="M10.6665 1.3335V4.00016"
				stroke="#717182"
				strokeWidth="1.33333"
				strokeLinecap="round"
				strokeLinejoin="round"
			/>
			<path
				d="M12.6667 2.6665H3.33333C2.59695 2.6665 2 3.26346 2 3.99984V13.3332C2 14.0696 2.59695 14.6665 3.33333 14.6665H12.6667C13.403 14.6665 14 14.0696 14 13.3332V3.99984C14 3.26346 13.403 2.6665 12.6667 2.6665Z"
				stroke="#717182"
				strokeWidth="1.33333"
				strokeLinecap="round"
				strokeLinejoin="round"
			/>
			<path
				d="M2 6.6665H14"
				stroke="#717182"
				strokeWidth="1.33333"
				strokeLinecap="round"
				strokeLinejoin="round"
			/>
		</svg>
	);

	const handleCopy = () => {
		const textToCopy = articles
			? articles.map((a) => `**${a.title}**\n${a.summary}`).join("\n\n")
			: content;
		navigator.clipboard.writeText(textToCopy);
		setCopied(true);
		setTimeout(() => setCopied(false), 2000);
	};

	return (
		<article className="w-fit h-fit items-center justify-center flex flex-col gap-7.5 px-10 py-10 rounded-[14px] bg-white">
			<header className="w-full flex flex-row flex-1 justify-between">
				<div className="flex flex-col gap-2">
					<h4>{title}</h4>
					<p className="flex items-center gap-2 text-slate-800">
						{calIcon} {formattedDate}
					</p>
					{articles && (
						<p className="text-body-xs text-slate-600">
							{articles.length} article(s)
						</p>
					)}
				</div>
				<Button onClick={handleCopy}>{copied ? "Copié !" : "Copier"}</Button>
			</header>
			{description && (
				<p className="text-body-s text-slate-800 font-medium">{description}</p>
			)}
			<div className="text-slate-dark wrap-normal text-body-s w-full">
				{articles ? (
					<div className="flex flex-col gap-6">
						{articles.map((article) => (
							<div
								key={article.title}
								className="border-l-2 border-slate-300 pl-4"
							>
								<h5 className="font-semibold">{article.title}</h5>
								<p className="mt-1">{article.summary}</p>
								{article.source && (
									<a
										href={article.source}
										target="_blank"
										rel="noopener noreferrer"
										className="text-brand-velvet text-body-xs mt-1 inline-block"
									>
										Source
									</a>
								)}
							</div>
						))}
					</div>
				) : (
					<Markdown components={markdownComponents}>{content}</Markdown>
				)}
			</div>
		</article>
	);
}
