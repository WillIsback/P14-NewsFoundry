
interface InputProps {
  label : string
  placeholder : string
  type? : "text" | "password" | "email"
}

export default function Input(props: Readonly<InputProps>) {
  const { label, placeholder, type } = props;


  return (
    <label className="h-fit flex flex-col gap-3">{label}
      <input 
        name = {label.trim().toLowerCase()}
        placeholder={placeholder} 
        type={type}
        className="w-full min-h-9 px-3 py-1 rounded-[8px] bg-slate-300 border-2 border-transparent focus:border-brand-velvet
        placeholder:text-body-xs placeholder:text-slate-800
        focus:outline-none focus:placeholder:text-transparent transition-colors duration-200
        focus:cursor-text"
      />
    </label>
  )
}