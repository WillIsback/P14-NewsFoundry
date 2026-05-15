import { Suspense } from "react";
import { fetchChats } from "@/src/actions/chat.action";
import { fetchReviews } from "@/src/actions/review.action";
import AssistantCard from "@/src/components/AssistantCard";
import ChatForm from "@/src/components/ChatForm";
import DisplayReviews from "@/src/components/DisplayReviews";
import { ErrorBoundary } from "@/src/components/ErrorBoundary";
import Menu from "@/src/components/Menu";
import { MenuDrawer } from "@/src/components/MenuDrawer";
import { SubMenuNav } from "@/src/components/SubMenuNav";

export default async function HomePage({
	searchParams,
}: Readonly<{ searchParams: Promise<{ mode?: string }> }>) {
	const { mode } = await searchParams;
	const defaultMode = mode === "review" ? "review" : "chat";

	const chatsPromise = fetchChats().then((r) => {
		if (r.error || !r.data) throw new Error(r.error ?? "Failed to load chats");
		return r.data.data ?? [];
	});

	const reviewsPromise = fetchReviews().then((r) => {
		if (r.error || !r.data)
			throw new Error(r.error ?? "Failed to load reviews");
		return r.data.data ?? [];
	});

	return (
		<div className="flex w-full h-full">
			<ErrorBoundary
				fallback={
					<aside className="hidden tablet:flex w-fit h-full bg-slate-100" />
				}
			>
				<Suspense
					fallback={
						<aside className="hidden tablet:flex w-fit h-full bg-slate-100" />
					}
				>
					<Menu chatsPromise={chatsPromise} />
				</Suspense>
			</ErrorBoundary>
			{/* Main content area */}
			<div className=" w-full h-full flex flex-col">
				<header className="w-full h-22 flex justify-between items-center px-4.5 py-1.75 bg-slate-100 border-0 border-l border-b border-slate-400">
					<Suspense>
						<SubMenuNav defaultMode={defaultMode} />
					</Suspense>
					<Suspense>
						<MenuDrawer chatsPromise={chatsPromise} />
					</Suspense>
				</header>
				{/* Assistant response area */}

				<section
					className={`w-full flex-1 min-h-0 flex flex-col gap-2.5 bg-slate-400 ${defaultMode === "review" ? "px-4 md:px-22.5 pt-6 md:pt-10" : "px-4 py-8 md:px-[25%] md:py-[18%]"}`}
				>
					{defaultMode === "review" ? (
						<ErrorBoundary
							fallback={
								<p className="text-slate-100">
									Impossible de charger les revues de presse.
								</p>
							}
						>
							<Suspense
								fallback={
									<p className="text-slate-100">Chargement des revues...</p>
								}
							>
								<DisplayReviews reviewsPromise={reviewsPromise} />
							</Suspense>
						</ErrorBoundary>
					) : (
						<AssistantCard variant="welcome" />
					)}
				</section>
				{defaultMode === "chat" && <ChatForm mode="new" />}
			</div>
		</div>
	);
}
