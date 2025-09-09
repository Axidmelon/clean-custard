import { useTheme } from "next-themes"
import { Toaster as Sonner } from "sonner"

import { sonnerToastOptions } from "./sonner-constants"
import { toast } from "./sonner-utils"

type ToasterProps = React.ComponentProps<typeof Sonner>

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme()

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      toastOptions={sonnerToastOptions}
      {...props}
    />
  )
}

export { Toaster }
