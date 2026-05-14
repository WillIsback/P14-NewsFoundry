import { promises as fs } from "node:fs";
import { Suspense } from "react";
import AssistantCard from "@/src/components/AssistantCard";
import Menu from "@/src/components/Menu";
import { SubMenuNav } from "@/src/components/SubMenuNav";
import { ButtonSend } from "@/src/components/ui/ButtonSend";
import TextArea from "@/src/components/ui/TextArea";
import DisplayReviews from "@/src/components/DisplayReviews";

export default async function HomePage({
	searchParams,
}: Readonly<{ searchParams: Promise<{ mode?: string }> }>) {
	const { mode } = await searchParams;
	const defaultMode = mode === "review" ? "review" : "chat";
	let chats: { id: string; date: string }[] | undefined;
	let pressReviews:
		| { id: string; title: string; description: string; content: string }[]
		| undefined
	try {
		const file = await fs.readFile(
			`${process.cwd()}/data/mockData.json`,
			"utf8",
		);
		const data = JSON.parse(file);
		chats = data.chats;
		pressReviews = data.pressReviews;
	} catch {
		chats = undefined;
		pressReviews = undefined;
	}

	return (
		<div className="flex w-full h-full">
			<Menu chats={chats} />
			{/* Main content area */}
			<div className=" w-full h-full flex flex-col">
				<header className="w-full h-22 flex items-center px-4.5 py-1.75 bg-slate-100 border-0 border-l border-b border-slate-400">
					<Suspense>
						<SubMenuNav defaultMode={defaultMode} />
					</Suspense>
				</header>
				{/* Assistant response area */}

				<section className={`w-full flex-1 min-h-0 flex flex-col gap-2.5 bg-slate-400 ${defaultMode === "review" ? "px-22.5 pt-10 " : "px-[25%] py-[18%]"}`}>
					{defaultMode ==="review" 
						? <DisplayReviews pressReviews={pressReviews} />
						: <AssistantCard variant="welcome" />}
				</section>
				<footer className="flex w-full min-h-23.25 gap-4 px-[6.44%] py-4.25 bg-white">
					<TextArea />
					<ButtonSend disabled={defaultMode === "review"} />
				</footer>
			</div>
		</div>
	);
}
