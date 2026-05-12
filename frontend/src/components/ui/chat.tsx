interface ChatProps  {
    date : string
}
export default function Chat (props : Readonly<ChatProps>){
  return (
    <li className="w-full h-fit flex flex-col items-center gap-1 px-6 py-5.25 border border-slate-300">
        <h3 className="text-body-s text-slate-dark">Discussion du</h3>
        <span>{props.date}</span>
    </li>
  )
}



