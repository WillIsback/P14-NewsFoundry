"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ButtonSubMenu } from "@/src/components/ui/ButtonSubMenu";

interface SubMenuNavProps {
	defaultMode?: "chat" | "review";
}

export function SubMenuNav({
	defaultMode = "chat",
}: Readonly<SubMenuNavProps>) {
	const params = useSearchParams();
	const mode = (params.get("mode") as "chat" | "review") ?? defaultMode;

	return (
		<div className="w-fit h-fit flex items-center gap-2 rounded-[8px]">
			<Link href="/home">
				<ButtonSubMenu type_="chat" active={mode === "chat"} />
			</Link>
			<Link href="/home?mode=review">
				<ButtonSubMenu type_="review" active={mode === "review"} />
			</Link>
		</div>
	);
}
