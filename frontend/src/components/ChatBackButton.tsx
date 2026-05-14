"use client";

import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";

export function ChatBackButton() {
	const router = useRouter();

	return (
		<button
			type="button"
			onClick={() => router.back()}
			className="flex h-22 w-50 items-center gap-2 hover:font-bold hover:cursor-pointer"
		>
			<ArrowLeft size={18} />
			<div className="flex flex-col gap-1">
				<h3 className="text-slate-dark">Nouvelle discussion</h3>
				<small className="text-slate-600">Conversation active</small>
			</div>
		</button>
	);
}
