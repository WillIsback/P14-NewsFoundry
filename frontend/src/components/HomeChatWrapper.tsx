"use client";

import { useActionState, useEffect, useState } from "react";
import {
	type ChatActionState,
	sendNewMessage,
} from "@/src/actions/chat.action";
import AssistantCard from "./AssistantCard";
import ChatForm from "./ChatForm";

const initialState: ChatActionState = { error: null };

export default function HomeChatWrapper() {
	const [state, formAction, isPending] = useActionState<
		ChatActionState & { data?: unknown },
		FormData
	>(sendNewMessage, initialState);

	const [resetKey, setResetKey] = useState(0);

	useEffect(() => {
		if (!isPending && !state.error && state.data !== undefined) {
			setResetKey((k) => k + 1);
		}
	}, [isPending, state]);

	return (
		<>
			<section className="w-full flex-1 min-h-0 flex flex-col gap-2.5 px-4 py-8 md:px-[25%] md:py-[18%] bg-slate-400">
				<AssistantCard variant={isPending ? "pending" : "welcome"} />
			</section>
			<ChatForm
				key={resetKey}
				formAction={formAction}
				isPending={isPending}
				error={state.error}
			/>
		</>
	);
}
