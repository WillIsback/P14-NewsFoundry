import PressReview from "./PressReview";

export default function DisplayReviews({
	pressReviews,
}: Readonly<{
	pressReviews?: {
		id: string;
		title: string;
		description: string;
		content: string;
	}[];
}>) {
	return (
		<div className="flex flex-col h-full min-h-0">
			<header className="flex flex-col h-fit w-full shrink-0">
				<h1 className="text-2xl font-bold">Revues de Presse</h1>
				<p className="text-slate-600">
					Consultez et férez vos revues de presse générées par l&apos;IA
				</p>
			</header>
			{/* PressReviews Gallery display */}
			<div className="flex-1 overflow-y-auto flex flex-col gap-4 mt-4 [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-slate-300 [&::-webkit-scrollbar-thumb]:rounded-full">
				{pressReviews?.map((review) => (
					<PressReview key={review.id} {...review} />
				))}
			</div>
		</div>
	);
}
