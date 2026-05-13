import { cva, type VariantProps } from "class-variance-authority"

const chatVariant = cva(
  "w-full h-fit flex flex-col items-center gap-1 px-6 py-5.25",
  {
    variants: {
      variant: {
        default: "bg-slate-100",
        hover:
          "border-border bg-background shadow-xs hover:bg-muted hover:text-foreground aria-expanded:bg-muted aria-expanded:text-foreground dark:border-input dark:bg-input/30 dark:hover:bg-input/50",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)
interface ChatProps  {
    date : string
}

export default function Chat (props : Readonly<ChatProps>){
  return (
    <li className="w-full h-fit flex flex-col gap-1 px-6 py-5.25 border border-slate-300 hover:bg-slate-300 hover:border-0">
        <h3 className="text-body-s text-slate-dark">Discussion du</h3>
        <span>{props.date}</span>
    </li>
  )
}



