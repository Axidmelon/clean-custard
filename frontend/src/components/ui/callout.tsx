import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const calloutVariants = cva(
  "relative w-full rounded-lg border p-4 [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground",
  {
    variants: {
      variant: {
        default: "bg-background text-foreground border-border",
        destructive: "border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive",
        warning: "border-yellow-500/50 text-yellow-600 dark:border-yellow-500 [&>svg]:text-yellow-600 bg-yellow-50/50 dark:bg-yellow-950/20",
        info: "border-blue-500/50 text-blue-600 dark:border-blue-500 [&>svg]:text-blue-600 bg-blue-50/50 dark:bg-blue-950/20",
        success: "border-green-500/50 text-green-600 dark:border-green-500 [&>svg]:text-green-600 bg-green-50/50 dark:bg-green-950/20",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface CalloutProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof calloutVariants> {
  icon?: React.ReactNode
}

const Callout = React.forwardRef<HTMLDivElement, CalloutProps>(
  ({ className, variant, icon, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        role="alert"
        className={cn(calloutVariants({ variant }), className)}
        {...props}
      >
        {icon}
        <div className="[&_p]:leading-relaxed">
          {children}
        </div>
      </div>
    )
  }
)
Callout.displayName = "Callout"

const CalloutTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h5
    ref={ref}
    className={cn("mb-1 font-medium leading-none tracking-tight", className)}
    {...props}
  />
))
CalloutTitle.displayName = "CalloutTitle"

const CalloutDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("text-sm [&_p]:leading-relaxed", className)}
    {...props}
  />
))
CalloutDescription.displayName = "CalloutDescription"

export { Callout, CalloutTitle, CalloutDescription }
