interface ChipsProps {
	// Define any props if needed
	categorie: string;
	variant?: "default" | "tag";
}

export default function Chips({ categorie, variant }: Readonly<ChipsProps>) {
	return (
		<button
			type="button"
			className={`w-[68.44px] h-5.5 rounded-[8px] flex gap-1 px-2 py-1 items-center justify-center text-slate-dark ${variant === "default" ? "bg-slate-300" : "bg-slate-100 border border-black"}`}
			disabled={variant === "tag"}
		>
			<span>{categorie}</span>
		</button>
	);
}
