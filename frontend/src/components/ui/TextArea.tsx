export default function TextArea() {
	return (
		<>
			{/* Label visually hidden — the placeholder serves as visual hint */}
			<label htmlFor="chat-message" className="sr-only">
				Message
			</label>
			<textarea
				id="chat-message"
				className="w-full min-h-15 px-3 py-2 rounded-[8px] bg-slate-200 border border-transparent focus:border-brand-velvet
          placeholder:text-body-xs placeholder:text-slate-800
          focus:outline-none focus:placeholder:text-transparent transition-colors duration-200
          focus:cursor-text"
				placeholder="Tapez votre message ici..."
				name="content"
			/>
		</>
	);
}
