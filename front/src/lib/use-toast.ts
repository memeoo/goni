import toast from 'react-hot-toast'

interface ToastOptions {
  title: string
  description: string
  variant?: 'default' | 'destructive'
}

export const useToast = () => {
  const showToast = (options: ToastOptions) => {
    const { title, description, variant = 'default' } = options
    const message = `${title}: ${description}`

    if (variant === 'destructive') {
      toast.error(message)
    } else {
      toast.success(message)
    }
  }

  return {
    toast: showToast,
  }
}
