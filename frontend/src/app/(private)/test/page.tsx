import { fetchChats } from "@/src/actions/chat.action";
import { ErrorBoundary } from "@/src/components/ErrorBoundary";
import Menu from "@/src/components/Menu";
import PressReview from "@/src/components/PressReview";
import { ButtonReview } from "@/src/components/ui/ButtonReview";
import { ButtonSend } from "@/src/components/ui/ButtonSend";
import { ButtonSubMenu } from "@/src/components/ui/ButtonSubMenu";
import Chips from "@/src/components/ui/Chips";
import Icon from "@/src/components/ui/Icon";
import Input from "@/src/components/ui/Input";
import Logo from "@/src/components/ui/Logo";
import Message from "@/src/components/ui/Message";
import Robot from "@/src/components/ui/Robot";
import TextArea from "@/src/components/ui/TextArea";

export default async function TestPage() {
	let pressReviews:
		| { id: string; title: string; description: string; content: string }[]
		| undefined;
	let messages:
		| { id: string; type: "user" | "ai"; content: string; timestamp: string }[]
		| undefined;

	const chatsPromise = fetchChats().then((r) => {
		if (r.error || !r.data) throw new Error(r.error ?? "Failed to load chats");
		return r.data.data ?? [];
	});

	return (
		<div className="h-max bg-[#343434] flex gap-50 flex-wrap px-12 py-12">
			<div className="flex flex-col gap-4">
				<h2 className="border border-brand-velvet rounded-l px-4 py-4">
					Menu ui{" "}
				</h2>
				<ErrorBoundary
					fallback={
						<aside className="hidden tablet:flex w-fit h-full bg-slate-100" />
					}
				>
					<Menu chatsPromise={chatsPromise} />
				</ErrorBoundary>
			</div>

			<div className="flex flex-col gap-4">
				<h2 className="border border-brand-velvet rounded-l px-4 py-4">
					Input ui{" "}
				</h2>
				<Input label="Email" placeholder="Enter your email" type="email" />
			</div>

			<div className="flex flex-col gap-4">
				<h2 className="border border-brand-velvet rounded-l px-4 py-4">
					Robot & Logo
				</h2>
				<div className="bg-white flex gap-4 justify-center items-center p-4 rounded">
					<div className="flex flex-col gap-4">
						<Robot variant="default" />
						<Robot variant="variant" />
					</div>
					<Logo />
				</div>
			</div>

			<div className="flex flex-col gap-4">
				<h2 className="border border-brand-velvet rounded-l px-4 py-4">
					Press Review
				</h2>
				{pressReviews?.map((review) => (
					<PressReview key={review.id} {...review} />
				))}
			</div>

			<div className="flex flex-col gap-4">
				<h2 className="border border-brand-velvet rounded-l px-4 py-4">Icon</h2>
				<Icon type="user" />
				<Icon type="ai" />
			</div>

			<div className="flex flex-col gap-4">
				<h2 className="border border-brand-velvet rounded-l px-4 py-4">
					Messages
				</h2>
				{messages?.map((message) => (
					<Message key={message.id} {...message} />
				))}
			</div>

			<div className="flex flex-col gap-4">
				<h2 className="border border-brand-velvet rounded-l px-4 py-4">
					TextArea
				</h2>
				<TextArea />
			</div>

			<div className="flex flex-col gap-4">
				<h2 className="border border-brand-velvet rounded-l px-4 py-4">
					ButtonSend
				</h2>
				<ButtonSend />
			</div>

			<div className="flex flex-col gap-4">
				<h2 className="border border-brand-velvet rounded-l px-4 py-4">
					ButtonSubMenu
				</h2>
				<ButtonSubMenu type_="chat" active />
				<ButtonSubMenu type_="review" />
			</div>

			<div className="flex flex-col gap-4 bg-white">
				<h2 className="border border-brand-velvet rounded-l px-4 py-4">
					Chips
				</h2>
				<Chips categorie="Politique" variant="default" />
				<Chips categorie="Economie" variant="default" />
				<Chips categorie="Sport" variant="default" />
				<Chips categorie="Culture" variant="default" />
				<Chips categorie="Tag1" variant="tag" />
				<Chips categorie="Tag2" variant="tag" />
			</div>

			<div className="flex flex-col gap-4">
				<h2 className="border border-brand-velvet rounded-l px-4 py-4">
					ButtonReview
				</h2>
				<ButtonReview />
			</div>
		</div>
	);
}
