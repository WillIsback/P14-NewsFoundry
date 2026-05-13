export default function TextArea() {
    return (
        <textarea 
          className="w-full min-h-15 px-3 py-2 rounded-[8px] bg-slate-200 border border-transparent focus:border-brand-velvet
          placeholder:text-body-xs placeholder:text-slate-800
          focus:outline-none focus:placeholder:text-transparent transition-colors duration-200
          focus:cursor-text"
          placeholder="Tapez votre message ici..."
          name="textarea"
        />
    )
}