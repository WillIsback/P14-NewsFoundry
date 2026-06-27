/**
 * Props for the Input component.
 *
 * @property label - The label text displayed above the input field.
 * @property placeholder - Placeholder text shown when the input is empty.
 * @property type - The input type: `"text"`, `"password"`, or `"email"`. Defaults to `"text"`.
 * @property name - The HTML name attribute. Derived from label if omitted.
 * @property autocomplete - The autocomplete attribute. Auto-detected based on type if omitted.
 * @property required - Whether the field is required. Defaults to `false`.
 */
interface InputProps {
	label: string;
	placeholder: string;
	type?: "text" | "password" | "email";
	name?: string;
	autocomplete?: string;
	required?: boolean;
}

/**
 * A labeled form input field with auto-detected autocomplete and smart styling.
 *
 * Automatically sets the autocomplete attribute based on input type (email, password, etc.)
 * and derives the name from the label if not provided.
 */
export default function Input(props: Readonly<InputProps>) {
	const { label, placeholder, type, required, name, autocomplete } = props;

	const autoAttr =
		autocomplete ??
		(type === "password"
			? "current-password"
			: type === "email"
				? "email"
				: undefined);

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
