import { Loader2, WandSparkles } from "lucide-react";

export default function AssistantPendingContent() {
	return (
		<>
			<WandSparkles size={48} className="text-brand-velvet" />
			<div
				role="status"
				aria-label="Chargement en cours"
				className="flex items-center gap-3"
			>
				<Loader2 size={24} className="animate-spin text-brand-velvet" />
			</div>
			<p className="text-center text-slate-700">
				Création de votre chat et recherche des actualités en cours…
			</p>
		</>
	);
}
