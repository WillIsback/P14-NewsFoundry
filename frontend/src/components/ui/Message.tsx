import { format } from "date-fns";
import { fr } from "date-fns/locale";
import Markdown, { type Components } from "react-markdown";

const markdownComponents: Components = {
	ul: ({ children }) => (
		<ul className="list-disc list-inside my-2">{children}</ul>
	),
	ol: ({ children }) => (
		<ol className="list-decimal list-inside my-2">{children}</ol>
	),
};

/**
 * Props for the Message component.
 *
 * @property type - The message source: `"user"` for user messages, `"ai"` for assistant responses.
 * @property content - The message text content. Rendered as plain text for users, Markdown for AI.
 * @property timestamp - ISO 8601 timestamp. Displayed formatted as `HH:mm` in French locale.
 */
interface MessageProps {
	type: "user" | "ai";
	content?: string;
	timestamp?: string;
}

/**
 * Displays a chat message — user or AI — with formatted timestamp.
 *
 * User messages appear on the right (dark background), AI messages on the left (light background).
 * AI messages support Markdown rendering with custom list styles.
 *
 * @param type - The message source: `"user"` or `"ai"`.
 * @param content - The message text. Markdown is rendered for AI messages only.
 * @param timestamp - ISO 8601 timestamp, formatted as `HH:mm` in French locale.
 */
export default function Message({
	type,
	content,
	timestamp,
}: Readonly<MessageProps>) {
	const formattedTimeStamp = timestamp
		? format(new Date(timestamp), "HH:mm", { locale: fr })
		: "";

	return (
		<div
			className={`flex flex-col h-fit justify-center gap-4 px-4 py-4 rounded-[10px] ${type === "user" ? "bg-slate-dark w-fit" : "bg-slate-300 w-full"}`}
		>
			{type === "user" ? (
				<>
					<p className="text-slate-white wrap-normal">{content}</p>
					<time className="text-slate-300">{formattedTimeStamp}</time>
				</>
			) : (
				<>
					<div className="text-slate-dark wrap-normal text-body-s">
						<Markdown components={markdownComponents}>{content}</Markdown>
					</div>
					<time className="text-[#717182]">{formattedTimeStamp}</time>
				</>
			)}
		</div>
	);
}
