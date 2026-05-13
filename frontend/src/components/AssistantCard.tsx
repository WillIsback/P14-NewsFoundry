import AssistantWelcome from "./ui/AssistantWelcome";
import Message from "./ui/Message";

interface AssistantCardProps {
	variant?: "default" | "welcome";
	messages?: {
		id: string;
		type: "user" | "ai";
		content?: string;
		timestamp?: string;
	}[];
}

export default function AssistantCard({
	variant,
	messages,
}: Readonly<AssistantCardProps>) {
	return (
		<div className="flex flex-col w-full h-fit items-center gap-10 px-10 py-14 rounded-[14px] bg-slate-white border border-slate-300">
			{variant === "welcome" ? (
				<AssistantWelcome />
			) : (
				// Render messages or other content for the "default" variant
				<div>
					{messages?.map((message) => (
						<Message
							key={message.id}
							type={message.type}
							content={message.content}
							timestamp={message.timestamp}
						/>
					))}
				</div>
			)}
		</div>
	);
}
