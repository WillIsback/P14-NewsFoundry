import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { Slot } from "radix-ui"

import { cn } from "@/src/lib/utils"

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <g clipPath="url(#clip0_11_1091)">
        <path
          d="M9.6907 14.4572C9.71603 14.5203 9.76006 14.5742 9.81688 14.6116C9.87371 14.6489 9.9406 14.668 10.0086 14.6663C10.0766 14.6646 10.1424 14.6421 10.1973 14.6018C10.2521 14.5616 10.2933 14.5055 10.3154 14.4412L14.6487 1.77454C14.67 1.71547 14.6741 1.65154 14.6604 1.59024C14.6468 1.52894 14.6159 1.4728 14.5715 1.42839C14.5271 1.38398 14.471 1.35314 14.4097 1.33947C14.3484 1.3258 14.2844 1.32987 14.2254 1.35121L1.5587 5.68454C1.49436 5.7066 1.43832 5.74782 1.39808 5.80266C1.35785 5.85749 1.33535 5.92332 1.33361 5.99131C1.33186 6.05931 1.35096 6.1262 1.38834 6.18303C1.42571 6.23985 1.47958 6.28388 1.5427 6.30921L6.82937 8.42921C6.99649 8.49612 7.14833 8.59618 7.27574 8.72336C7.40315 8.85054 7.50349 9.0022 7.5707 9.16921L9.6907 14.4572Z"
          stroke="currentColor" strokeWidth="1.33333" strokeLinecap="round" strokeLinejoin="round"
        />
        <path
          d="M14.5693 1.43115L7.276 8.72382"
          stroke="currentColor" strokeWidth="1.33333" strokeLinecap="round" strokeLinejoin="round"
        />
      </g>
      <defs>
        <clipPath id="clip0_11_1091">
          <rect width="16" height="16" fill="white" />
        </clipPath>
      </defs>
    </svg>
  )
}

const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center rounded-md border border-transparent bg-clip-padding text-sm font-medium whitespace-nowrap transition-all outline-none select-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 active:not-aria-[haspopup]:translate-y-px disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default: "bg-brand-velvet text-slate-white hover:bg-slate-dark disabled:text-slate-200 disabled:bg-slate-500 disabled:opacity-100",
        outline:
          "border-border bg-background shadow-xs hover:bg-muted hover:text-foreground aria-expanded:bg-muted aria-expanded:text-foreground dark:border-input dark:bg-input/30 dark:hover:bg-input/50",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80 aria-expanded:bg-secondary aria-expanded:text-secondary-foreground",
        ghost:
          "hover:bg-muted hover:text-foreground aria-expanded:bg-muted aria-expanded:text-foreground dark:hover:bg-muted/50",
        destructive:
          "bg-destructive/10 text-destructive hover:bg-destructive/20 focus-visible:border-destructive/40 focus-visible:ring-destructive/20 dark:bg-destructive/20 dark:hover:bg-destructive/30 dark:focus-visible:ring-destructive/40",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default:
          "h-10 w-12 in-data-[slot=button-group]:rounded-[8px] ",
        xs: "h-6 gap-1 rounded-[min(var(--radius-md),8px)] px-2 text-xs in-data-[slot=button-group]:rounded-md has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3",
        sm: "h-8 gap-1 rounded-[min(var(--radius-md),10px)] px-2.5 in-data-[slot=button-group]:rounded-md has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5",
        lg: "h-10 gap-1.5 px-2.5 has-data-[icon=inline-end]:pr-2 has-data-[icon=inline-start]:pl-2",
        icon: "size-9",
        "icon-xs":
          "size-6 rounded-[min(var(--radius-md),8px)] in-data-[slot=button-group]:rounded-md [&_svg:not([class*='size-'])]:size-3",
        "icon-sm":
          "size-8 rounded-[min(var(--radius-md),10px)] in-data-[slot=button-group]:rounded-md",
        "icon-lg": "size-10",
      },

    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function ButtonSend({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  children,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot.Root : "button"

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    >
      {children ?? <SendIcon />}
    </Comp>
  )
}

export { ButtonSend, buttonVariants }
