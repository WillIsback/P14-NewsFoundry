"use client";

import { useActionState, useEffect, useState } from "react";
import {
	type ChatActionState,
	sendNewMessage,
} from "@/src/actions/chat.action";
import ChatForm from "./ChatForm";

const initialState: ChatActionState = { error: null };

export default function NewChatFormWrapper() {
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
		<ChatForm
			key={resetKey}
			formAction={formAction}
			isPending={isPending}
			error={state.error}
		/>
	);
}
