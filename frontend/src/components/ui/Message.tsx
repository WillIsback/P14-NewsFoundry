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

interface MessageProps {
	// Define any props if needed
	type: "user" | "ai";
	content?: string;
	timestamp?: string;
}

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
