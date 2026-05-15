import { notFound } from "next/navigation";
import { Suspense } from "react";
import { fetchChats, fetchMessages } from "@/src/actions/chat.action";
import AssistantCard from "@/src/components/AssistantCard";
import ChatForm from "@/src/components/ChatForm";
import { ChatHeader } from "@/src/components/ChatHeader";
import Menu from "@/src/components/Menu";

export default async function ChatPage({
	params,
}: Readonly<{
	params: Promise<{ slug: string }>;
}>) {
	const { slug } = await params;
	const chatId = Number.parseInt(slug, 10);
	if (Number.isNaN(chatId)) notFound();

	const chatsPromise = fetchChats().then((r) => {
		if (r.error || !r.data) throw new Error(r.error ?? "Failed to load chats");
		return r.data.data ?? [];
	});

	const messagesResult = await fetchMessages(chatId);
	if (messagesResult.error) notFound();
	const messages = messagesResult.data?.data ?? [];

	return (
		<div className="flex w-full h-full">
			<Suspense
				fallback={
					<aside className="hidden tablet:flex w-fit h-full bg-slate-100" />
				}
			>
				<Menu chatsPromise={chatsPromise} />
			</Suspense>
			{/* Main content area */}
			<div className=" w-full h-full flex flex-col">
				{/* Partie Header */}
				<ChatHeader />
				{/* Assistant response area */}
				{/* Home Assistant Chat Section */}
				<section className="w-full flex-1 min-h-0 flex flex-col gap-2.5 px-4 py-8 md:px-[25%] md:py-[18%] bg-slate-400">
					<AssistantCard messages={messages} />
				</section>
				<ChatForm mode="continue" chatId={chatId} />
			</div>
		</div>
	);
}
