interface InputProps {
	label: string;
	placeholder: string;
	type?: "text" | "password" | "email";
	name?: string;
	autocomplete?: string;
	required?: boolean;
}

export default function Input(props: Readonly<InputProps>) {
	const { label, placeholder, type, required, name, autocomplete } = props;

	const autoAttr =
		autocomplete ?? (type === "password" ? "current-password" : type === "email" ? "email" : undefined);

	return (
		<label className="w-full h-fit flex flex-col gap-3 text-slate-dark">
			{label}
			<input
				name={name ?? label.trim().toLowerCase().replace(/\s+/g, "_")}
				placeholder={placeholder}
				type={type}
				autoComplete={autoAttr}
				className="w-full min-h-9 px-3 py-1 rounded-[8px] bg-slate-300 border-2 border-transparent focus:border-brand-velvet
        placeholder:text-body-xs placeholder:text-slate-800
        focus:outline-none focus:placeholder:text-transparent transition-colors duration-200
        focus:cursor-text"
				required={required}
			/>
		</label>
	);
}
