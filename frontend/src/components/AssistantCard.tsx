"use client";

import AssistantPendingContent from "./ui/AssistantPendingContent";
import AssistantWelcome from "./ui/AssistantWelcome";
import Icon from "./ui/Icon";
import Message from "./ui/Message";

/**
 * Props for the AssistantCard component.
 *
 * @property variant - The display variant: `"welcome"` for greeting, `"pending"` for loading, `"default"` for messages.
 * @property messages - Array of chat messages (user and AI) to display.
 */
interface AssistantCardProps {
	variant?: "default" | "welcome" | "pending";
	messages?: {
		id: number;
		type: string;
		content: string;
		timestamp: string;
	}[];
}

/**
 * Displays chat messages with user and AI icons, or welcome/pending states.
 *
 * Renders messages in a scrollable list with appropriate styling and icons,
 * or shows welcome greeting or loading state based on the variant.
 */
export default function AssistantCard({
	variant,
	messages,
}: Readonly<AssistantCardProps>) {
	if (!messages && variant !== "welcome" && variant !== "pending")
		return <p></p>;
	return (
		<>
			{variant === "welcome" ? (
				<div className="flex flex-col w-full h-fit items-center gap-10 px-10 py-14 rounded-[14px] bg-slate-white border border-slate-300">
					<AssistantWelcome />
				</div>
			) : variant === "pending" ? (
				<div className="flex flex-col w-full h-fit items-center gap-10 px-10 py-14 rounded-[14px] bg-slate-white border border-slate-300">
					<AssistantPendingContent />
				</div>
			) : (
				<div className="flex flex-col w-full h-fit gap-8">
					{messages && messages.length > 0 ? (
						messages?.map((message) => (
							<div
								key={message.id}
								className={`flex gap-2.5 ${message.type === "user" ? "justify-end" : "justify-start"}`}
							>
								{message.type === "ai" && <Icon type="ai" />}
								<Message
									key={message.id}
									type={message.type as "user" | "ai"}
									content={message.content}
									timestamp={message.timestamp}
								/>
								{message.type === "user" && <Icon type="user" />}
							</div>
						))
					) : (
						<p className="text-slate-800 text-center">
							Aucun message pour le moment. Commencez la conversation en
							envoyant un message !
						</p>
					)}
				</div>
			)}
		</>
	);
}
