import Link from "next/link";

export default function NotFound() {
	return (
		<div className="flex flex-col items-center justify-center h-full gap-4 text-center">
			<h1 className="text-2xl font-bold text-slate-dark">
				Conversation introuvable
			</h1>
			<p className="text-slate-800">
				La conversation demandée n&apos;existe pas ou a été supprimée.
			</p>
			<Link
				href="/home"
				className="text-brand-velvet underline underline-offset-4 hover:opacity-80 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-velvet rounded"
			>
				Retour à l&apos;accueil
			</Link>
		</div>
	);
}
