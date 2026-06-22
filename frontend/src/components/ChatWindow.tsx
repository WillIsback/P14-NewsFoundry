"use client";

import {
	startTransition,
	useActionState,
	useEffect,
	useOptimistic,
	useRef,
	useState,
} from "react";
import { type ChatActionState, continueChat } from "@/src/actions/chat.action";
import AssistantCard from "./AssistantCard";
import ChatForm from "./ChatForm";
import PendingSpinner from "./ui/PendingSpinner";

type Message = {
	id: number;
	type: string;
	content: string;
	timestamp: string;
};

type ChatWindowProps = {
	chatId: number;
	messages: Message[];
};

export default function ChatWindow({
	chatId,
	messages,
}: Readonly<ChatWindowProps>) {
	const [state, serverFormAction, isPending] = useActionState<
		ChatActionState & { data?: unknown },
		FormData
	>(continueChat.bind(null, chatId), { error: null });

	const [optimisticMessages, addOptimistic] = useOptimistic(
		messages,
		(current: Message[], newMsg: Message) => [...current, newMsg],
	);

	const [resetKey, setResetKey] = useState(0);
	const messagesEndRef = useRef<HTMLDivElement>(null);

	// biome-ignore lint/correctness/useExhaustiveDependencies: scroll on message/pending change is intentional
	useEffect(() => {
		if (typeof messagesEndRef.current?.scrollIntoView === "function") {
			messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
		}
	}, [optimisticMessages, isPending]);

	useEffect(() => {
		if (!isPending && !state.error && state.data !== undefined) {
			setResetKey((k) => k + 1);
		}
	}, [isPending, state]);

	function handleSubmit(formData: FormData) {
		const text = formData.get("content") as string;
		startTransition(() => {
			addOptimistic({
				id: Date.now(),
				type: "user",
				content: text,
				timestamp: new Date().toISOString(),
			});
			serverFormAction(formData);
		});
	}

	return (
		<>
			<section className="w-full flex-1 min-h-0 flex flex-col gap-2.5 px-4 py-8 md:px-[25%] md:py-[18%] bg-slate-400 overflow-y-auto">
				<AssistantCard messages={optimisticMessages} />
				{isPending && <PendingSpinner />}
				<div ref={messagesEndRef} />
			</section>
			<ChatForm
				key={resetKey}
				formAction={handleSubmit}
				isPending={isPending}
				error={state.error}
			/>
		</>
	);
}
