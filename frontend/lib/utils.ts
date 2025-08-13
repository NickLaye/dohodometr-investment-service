import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(
  amount: number,
  currency: string = 'RUB',
  locale: string = 'ru-RU'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency,
  }).format(amount)
}

export function formatPercentage(
  value: number,
  decimals: number = 2,
  locale: string = 'ru-RU'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value / 100)
}

export function formatNumber(
  value: number,
  locale: string = 'ru-RU'
): string {
  return new Intl.NumberFormat(locale).format(value)
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// Валидация пароля
export function validatePassword(password: string): {
  isValid: boolean
  errors: string[]
  strength: 'weak' | 'medium' | 'strong'
} {
  const errors: string[] = []
  
  if (password.length < 8) {
    errors.push('Пароль должен содержать минимум 8 символов')
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Пароль должен содержать заглавную букву')
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Пароль должен содержать строчную букву')
  }
  
  if (!/\d/.test(password)) {
    errors.push('Пароль должен содержать цифру')
  }
  
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('Пароль должен содержать специальный символ')
  }
  
  let strength: 'weak' | 'medium' | 'strong' = 'weak'
  
  if (errors.length === 0 && password.length >= 12) {
    strength = 'strong'
  } else if (errors.length <= 2) {
    strength = 'medium'
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    strength
  }
}