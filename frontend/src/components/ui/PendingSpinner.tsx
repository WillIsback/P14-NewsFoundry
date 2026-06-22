import { Loader2 } from "lucide-react";
import Icon from "./Icon";

export default function PendingSpinner() {
	return (
		<div className="flex gap-2.5 justify-start">
			<Icon type="ai" />
			<div
				role="status"
				aria-label="Chargement de la réponse"
				className="flex items-center px-4 py-4 rounded-[10px] bg-slate-300"
			>
				<Loader2 className="animate-spin text-slate-dark" size={20} />
			</div>
		</div>
	);
}
