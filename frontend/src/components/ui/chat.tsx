import Link from "next/link";

interface ChatProps {
	date: string;
}

export default function Chat(props: Readonly<ChatProps>) {
	return (
		<li className="w-full h-fit flex flex-col gap-1 px-6 py-5.25 border border-slate-300 hover:bg-slate-300 hover:border-0">
			<Link href="#">
				<p>Discussion du</p>
				<time className="text-slate-800">{props.date}</time>
			</Link>
		</li>
	);
}
