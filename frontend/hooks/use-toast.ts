'use client'

import { useState, useCallback } from 'react'

interface Toast {
  id: string
  title: string
  description?: string
  variant?: 'default' | 'destructive' | 'success' | 'warning'
  duration?: number
}

interface ToastState {
  toasts: Toast[]
}

export function useToast() {
  const [state, setState] = useState<ToastState>({ toasts: [] })

  const toast = useCallback(({ ...props }: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9)
    const newToast: Toast = {
      id,
      duration: 5000,
      ...props,
    }

    setState((state) => ({
      toasts: [...state.toasts, newToast],
    }))

    // Auto dismiss
    setTimeout(() => {
      setState((state) => ({
        toasts: state.toasts.filter((t) => t.id !== id),
      }))
    }, newToast.duration)

    return id
  }, [])

  const dismiss = useCallback((toastId: string) => {
    setState((state) => ({
      toasts: state.toasts.filter((t) => t.id !== toastId),
    }))
  }, [])

  return {
    toast,
    dismiss,
    toasts: state.toasts,
  }
}