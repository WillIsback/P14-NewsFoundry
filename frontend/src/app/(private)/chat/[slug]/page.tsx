import { promises as fs } from "node:fs";
import { notFound } from "next/navigation";
import AssistantCard from "@/src/components/AssistantCard";
import { ChatHeader } from "@/src/components/ChatHeader";
import Menu from "@/src/components/Menu";
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
				<ChatHeader />
				{/* Assistant response area */}
				{/* Home Assistant Chat Section */}
				<section className="w-full flex-1 min-h-0 flex flex-col gap-2.5 px-4 py-8 md:px-[25%] md:py-[18%] bg-slate-400">
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
