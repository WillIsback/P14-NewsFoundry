import { ChatBackButton } from "./ChatBackButton";
import { ButtonReview } from "./ui/ButtonReview";

/**
 * Props for the ChatHeader component.
 *
 * @property chatId - The ID of the current chat.
 * @property articles - The list of articles discussed in the chat.
 */
interface ChatHeaderProps {
	chatId?: number;
	articles?: { title: string; url: string }[];
}

/**
 * The header bar for a chat page with back button and review button.
 */
export function ChatHeader({ chatId, articles }: Readonly<ChatHeaderProps>) {
	return (
		<div className="w-full h-22 flex justify-between items-center px-4.5 py-1.75 bg-slate-100 border-0 border-l border-b border-slate-400">
			<ChatBackButton />
			<ButtonReview chatId={chatId} articles={articles ?? []} />
		</div>
	);
}
