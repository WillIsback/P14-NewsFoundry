"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { generateReview } from "@/src/actions/review.action";

function ReviewIcon() {
	return (
		<svg
			width="12"
			height="15"
			viewBox="0 0 12 15"
			fill="none"
			xmlns="http://www.w3.org/2000/svg"
		>
			<title>Revue de presse</title>
			<path
				d="M8.13086 0.0136719C8.25885 0.039297 8.37799 0.101683 8.47168 0.195312L11.8047 3.5293C11.9296 3.65417 11.9998 3.82342 12 4V12.667C12 13.1973 11.7889 13.706 11.4141 14.0811C11.0391 14.4559 10.5302 14.6669 10 14.667H2C1.46968 14.6669 0.960933 14.4561 0.585938 14.0811C0.210966 13.706 2.52486e-07 13.1973 0 12.667V2C0.000172407 1.4698 0.211018 0.960857 0.585938 0.585938C0.960903 0.211145 1.46984 8.61611e-05 2 0H8L8.13086 0.0136719ZM2 1.33398C1.82346 1.33407 1.65421 1.40455 1.5293 1.5293C1.40443 1.65417 1.33416 1.82342 1.33398 2V12.667C1.33398 12.8438 1.40427 13.0136 1.5293 13.1387C1.65421 13.2634 1.82346 13.3339 2 13.334H10C10.1766 13.3339 10.3467 13.2635 10.4717 13.1387C10.5965 13.0137 10.667 12.8436 10.667 12.667V5.33398H8.66602C8.13582 5.33381 7.62687 5.12297 7.25195 4.74805C6.87716 4.37308 6.6661 3.86415 6.66602 3.33398V1.33398H2ZM8.66602 10C9.0341 10 9.33283 10.299 9.33301 10.667C9.33301 11.0352 9.03421 11.334 8.66602 11.334H3.33301C2.96497 11.3338 2.66602 11.0351 2.66602 10.667C2.66619 10.2991 2.96508 10.0002 3.33301 10H8.66602ZM8.66602 7.33398C9.03421 7.33398 9.33301 7.63279 9.33301 8.00098C9.33283 8.36902 9.0341 8.66797 8.66602 8.66797H3.33301C2.96508 8.66779 2.66619 8.36891 2.66602 8.00098C2.66602 7.6329 2.96497 7.33416 3.33301 7.33398H8.66602ZM4.66602 4.66699C5.03421 4.66699 5.33301 4.96579 5.33301 5.33398C5.33301 5.70217 5.03421 6.00098 4.66602 6.00098H3.33301C2.96497 6.0008 2.66602 5.70207 2.66602 5.33398C2.66602 4.9659 2.96497 4.66717 3.33301 4.66699H4.66602ZM8 3.33398C8.00009 3.51052 8.07057 3.67977 8.19531 3.80469C8.32018 3.92956 8.48944 3.99983 8.66602 4H10.3906L8 1.60938V3.33398Z"
				fill="currentColor"
			/>
		</svg>
	);
}

interface ButtonReviewProps {
	chatId?: number;
}

function ButtonReview({ chatId }: Readonly<ButtonReviewProps>) {
	const router = useRouter();
	const [step, setStep] = useState<"idle" | "form" | "loading">("idle");
	const [subject, setSubject] = useState("");
	const [error, setError] = useState<string | null>(null);
	const inputRef = useRef<HTMLInputElement>(null);

	const handleOpenForm = () => {
		if (!chatId) return;
		setStep("form");
		setError(null);
		setTimeout(() => inputRef.current?.focus(), 0);
	};

	const handleCancel = () => {
		setStep("idle");
		setSubject("");
		setError(null);
	};

	const handleGenerate = async () => {
		if (!chatId || step === "loading") return;
		setStep("loading");
		setError(null);
		try {
			const result = await generateReview(chatId, subject.trim() || undefined);
			if (result.error) {
				setError(result.error);
				setStep("form");
			} else {
				const reviewId = result.data?.data?.id;
				router.push(
					reviewId
						? `/home?mode=review#review-${reviewId}`
						: "/home?mode=review",
				);
			}
		} catch {
			setError("Erreur lors de la génération de la revue de presse");
			setStep("form");
		}
	};

	const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
		if (e.key === "Enter") handleGenerate();
		if (e.key === "Escape") handleCancel();
	};

	if (step === "idle") {
		return (
			<div className="flex flex-col items-end gap-1">
				<button
					type="button"
					onClick={handleOpenForm}
					disabled={!chatId}
					className="inline-flex items-center justify-center gap-2.5 rounded-[8px] w-fit h-fit transition-all bg-brand-velvet text-slate-100 hover:bg-slate-dark hover:cursor-pointer disabled:bg-slate-400 disabled:text-slate-600 disabled:opacity-100 px-3 py-3 text-body-xs tablet:px-6 tablet:py-5.25 tablet:text-body-s"
				>
					<ReviewIcon />
					Générer une revue de presse
				</button>
			</div>
		);
	}

	return (
		<div className="flex flex-col items-end gap-2">
			<div className="flex flex-col gap-2 p-3 rounded-[8px] border border-slate-200 bg-slate-50 w-72">
				<p className="text-body-xs text-slate-700 font-medium">
					Sujet de la revue (optionnel)
				</p>
				<input
					ref={inputRef}
					type="text"
					value={subject}
					onChange={(e) => setSubject(e.target.value)}
					onKeyDown={handleKeyDown}
					placeholder="Ex : intelligence artificielle, politique…"
					maxLength={200}
					disabled={step === "loading"}
					className="w-full rounded-[6px] border border-slate-300 px-2.5 py-1.5 text-body-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-velvet disabled:opacity-50"
				/>
				<div className="flex gap-2 justify-end">
					<button
						type="button"
						onClick={handleCancel}
						disabled={step === "loading"}
						className="px-3 py-1.5 rounded-[6px] text-body-xs text-slate-600 hover:bg-slate-100 disabled:opacity-50"
					>
						Annuler
					</button>
					<button
						type="button"
						onClick={handleGenerate}
						disabled={step === "loading"}
						className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] text-body-xs bg-brand-velvet text-slate-100 hover:bg-slate-dark disabled:bg-slate-400 disabled:text-slate-600"
					>
						{step === "loading" ? "Génération…" : "Générer"}
					</button>
				</div>
			</div>
			{error && <p className="text-red-500 text-body-xs">{error}</p>}
		</div>
	);
}

export { ButtonReview };
