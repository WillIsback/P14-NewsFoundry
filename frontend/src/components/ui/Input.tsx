
interface InputProps {
  label : string
  placeholder : string
  type? : "text" | "password" | "email"
}

export default function Input(props: Readonly<InputProps>) {
  const { label, placeholder, type } = props;


  return (
    <label className="text-body-s text-slate-dark">{label}
      <input 
        placeholder={placeholder} 
        type={type}
        className="w-full min-h-9 px-3 py-1 rounded-[8px] bg-slate-300 border
        placeholder:text-body-xs placeholder:text-slate-800 
        focus:border-[--color-brand-velvet] focus:ring-[--color-brand-velvet] focus:ring-1 focus:outline-none"
      />
    </label>
  )
}