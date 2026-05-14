import { format, isValid, parseISO } from "date-fns";
import Link from "next/link";

interface ChatProps {
	id: number;
	date: string;
}

function formatChatDate(raw: string): string {
	const parsed = parseISO(raw);
	if (isValid(parsed)) return format(parsed, "dd/MM/yyyy");
	const fallback = new Date(raw);
	if (isValid(fallback)) return format(fallback, "dd/MM/yyyy");
	return raw;
}

export default function Chat(props: Readonly<ChatProps>) {
	const formattedDate = formatChatDate(props.date);

	return (
		<li className="w-full h-fit flex flex-col gap-1 px-6 py-5.25 border border-slate-300 hover:bg-slate-300 hover:border-0">
			<Link
				href={`/chat/${props.id}`}
				className="w-full h-fit flex flex-col gap-1"
			>
				<p>Discussion du</p>
				<time className="text-slate-800" dateTime={props.date}>
					{formattedDate}
				</time>
			</Link>
		</li>
	);
}
