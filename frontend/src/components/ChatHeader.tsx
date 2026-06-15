import { ChatBackButton } from "./ChatBackButton";
import { ButtonReview } from "./ui/ButtonReview";

interface ChatHeaderProps {
	chatId?: number;
	articles?: { title: string; url: string }[];
}

export function ChatHeader({ chatId, articles }: Readonly<ChatHeaderProps>) {
	return (
		<div className="w-full h-22 flex justify-between items-center px-4.5 py-1.75 bg-slate-100 border-0 border-l border-b border-slate-400">
			<ChatBackButton />
			<ButtonReview chatId={chatId} articles={articles ?? []} />
		</div>
	);
}
