import { ChatBackButton } from "./ChatBackButton";
import { ButtonReview } from "./ui/ButtonReview";

export function ChatHeader() {
	return (
		<div className="w-full h-22 flex justify-between items-center px-4.5 py-1.75 bg-slate-100 border-0 border-l border-b border-slate-400">
			<ChatBackButton />
			<ButtonReview />
		</div>
	);
}
