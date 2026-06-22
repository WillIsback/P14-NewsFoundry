import { notFound } from "next/navigation";
import { Suspense } from "react";
import {
	fetchChatArticles,
	fetchChats,
	fetchMessages,
} from "@/src/actions/chat.action";
import { ChatHeader } from "@/src/components/ChatHeader";
import ChatWindow from "@/src/components/ChatWindow";
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
	// Suppress unhandledRejection: rejection is delegated to ErrorBoundary via use()
	chatsPromise.catch(() => {});

	const messagesResult = await fetchMessages(chatId);
	if (messagesResult.error) notFound();
	const messages = messagesResult.data?.data ?? [];

	const articlesResult = await fetchChatArticles(chatId);
	const articles = articlesResult.data;

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
				<ChatHeader chatId={chatId} articles={articles} />
				{/* Chat window with messages and form */}
				<ChatWindow chatId={chatId} messages={messages} />
			</div>
		</div>
	);
}
