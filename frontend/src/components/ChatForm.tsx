"use client";

import { useActionState, useEffect, useRef } from "react";
import {
	type ChatActionState,
	continueChat,
	sendNewMessage,
} from "@/src/actions/chat.action";
import { ButtonSend } from "@/src/components/ui/ButtonSend";
import TextArea from "@/src/components/ui/TextArea";

type ChatFormProps = { mode: "new" } | { mode: "continue"; chatId: number };

const initialState: ChatActionState = { error: null };

export default function ChatForm(props: Readonly<ChatFormProps>) {
	const action =
		props.mode === "continue"
			? continueChat.bind(null, props.chatId)
			: sendNewMessage;

	const [state, formAction, isPending] = useActionState<
		ChatActionState & { data?: unknown },
		FormData
	>(action, initialState);

	const formRef = useRef<HTMLFormElement>(null);

	useEffect(() => {
		if (!isPending && !state.error && state.data !== undefined) {
			formRef.current?.reset();
		}
	}, [isPending, state]);

	return (
		<form
			ref={formRef}
			action={formAction}
			className="flex w-full min-h-23.25 gap-4 px-[6.44%] py-4.25 bg-white"
		>
			{state.error && (
				<p role="alert" className="sr-only">
					{state.error}
				</p>
			)}
			<TextArea />
			<ButtonSend type="submit" aria-busy={isPending} disabled={isPending} />
		</form>
	);
}
