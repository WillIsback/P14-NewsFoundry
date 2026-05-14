import { promises as fs } from "node:fs";
import { notFound } from "next/navigation";
import AssistantCard from "@/src/components/AssistantCard";
import { ChatBackButton } from "@/src/components/ChatBackButton";
import Menu from "@/src/components/Menu";
import { ButtonReview } from "@/src/components/ui/ButtonReview";
import { ButtonSend } from "@/src/components/ui/ButtonSend";
import TextArea from "@/src/components/ui/TextArea";

export default async function ChatPage({
	params,
}: Readonly<{
	params: Promise<{ slug: string }>;
}>) {
	const { slug } = await params;
	let chats:
		| {
				id: string;
				date: string;
				messages: {
					id: string;
					type: "user" | "ai";
					content: string;
					timestamp: string;
				}[];
		  }[]
		| undefined;

	try {
		const file = await fs.readFile(
			`${process.cwd()}/data/mockData.json`,
			"utf8",
		);
		const data = JSON.parse(file);
		chats = data.chats;
	} catch {
		chats = undefined;
	}
	const chat = chats?.find((c) => c.id === slug);
	if (!chat) {
		notFound();
	}
	return (
		<div className="flex w-full h-full">
			<Menu chats={chats} />
			{/* Main content area */}
			<div className=" w-full h-full flex flex-col">
				{/* Partie Header */}
				<div className="w-full h-22 flex justify-between items-center px-4.5 py-1.75 bg-slate-100 border-0 border-l border-b border-slate-400 ">
					{/* Partie Nav return*/}
					<ChatBackButton />
					<ButtonReview />
				</div>
				{/* Assistant response area */}
				{/* Home Assistant Chat Section*/}
				<section className="w-full min-h-202.75 flex flex-col gap-2.5 px-[25%] py-[18%] bg-slate-400">
					<AssistantCard messages={chat.messages} />
				</section>
				<footer className="flex w-full min-h-23.25 gap-4 px-[6.44%] py-4.25 bg-white">
					<TextArea />
					<ButtonSend />
				</footer>
			</div>
		</div>
	);
}
