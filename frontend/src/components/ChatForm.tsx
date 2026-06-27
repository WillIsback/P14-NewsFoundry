"use client";

import { ButtonSend } from "@/src/components/ui/ButtonSend";
import TextArea from "@/src/components/ui/TextArea";

/**
 * Props for the ChatForm component.
 *
 * @property formAction - Server action to call when the form is submitted.
 * @property isPending - Whether the form submission is in progress.
 * @property error - Error message to display, if any.
 */
type ChatFormProps = {
	formAction: (payload: FormData) => void;
	isPending: boolean;
	error: string | null;
};

/**
 * A form component for composing and sending chat messages.
 *
 * Displays a textarea and a send button, with support for error messages and pending state.
 */
export default function ChatForm({
	formAction,
	isPending,
	error,
}: Readonly<ChatFormProps>) {
	return (
		<form
			action={formAction}
			className="flex w-full min-h-23.25 gap-4 px-[6.44%] py-4.25 bg-white"
		>
			{error && (
				<p role="alert" className="text-sm text-red-600 self-center">
					{error}
				</p>
			)}
			<TextArea />
			<ButtonSend type="submit" aria-busy={isPending} disabled={isPending} />
		</form>
	);
}
