'use client'

import React, { useState, useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

interface CurrencyInputProps {
  value: number
  onChange: (value: number) => void
  currency?: string
  placeholder?: string
  label?: string
  disabled?: boolean
  className?: string
  id?: string
  min?: number
  max?: number
  step?: number
  error?: string
  required?: boolean
}

export function CurrencyInput({
  value,
  onChange,
  currency = '₽',
  placeholder = 'Введите сумму',
  label,
  disabled = false,
  className,
  id,
  min = 0,
  max,
  step = 0.01,
  error,
  required = false
}: CurrencyInputProps) {
  const [displayValue, setDisplayValue] = useState('')
  const [isFocused, setIsFocused] = useState(false)

  // Format number for display
  const formatForDisplay = (num: number) => {
    if (num === 0) return ''
    return new Intl.NumberFormat('ru-RU', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(num)
  }

  // Parse display value to number
  const parseDisplayValue = (str: string) => {
    const cleaned = str.replace(/[^\d,.-]/g, '').replace(',', '.')
    const num = parseFloat(cleaned)
    return isNaN(num) ? 0 : num
  }

  // Update display value when prop value changes
  useEffect(() => {
    if (!isFocused) {
      setDisplayValue(formatForDisplay(value))
    }
  }, [value, isFocused])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue = e.target.value
    setDisplayValue(inputValue)
    
    // Parse and update the actual value
    const numericValue = parseDisplayValue(inputValue)
    
    // Apply constraints
    let constrainedValue = numericValue
    if (min !== undefined && constrainedValue < min) constrainedValue = min
    if (max !== undefined && constrainedValue > max) constrainedValue = max
    
    onChange(constrainedValue)
  }

  const handleFocus = () => {
    setIsFocused(true)
    // Show raw numeric value when focused
    if (value > 0) {
      setDisplayValue(value.toString())
    }
  }

  const handleBlur = () => {
    setIsFocused(false)
    // Format the display value when not focused
    setDisplayValue(formatForDisplay(value))
  }

  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined)

  return (
    <div className="space-y-2">
      {label && (
        <Label htmlFor={inputId} className={required ? 'after:content-["*"] after:ml-0.5 after:text-destructive' : ''}>
          {label}
        </Label>
      )}
      <div className="relative">
        <Input
          id={inputId}
          type="text"
          value={displayValue}
          onChange={handleInputChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            'pr-12 font-mono tabular-nums',
            error && 'border-destructive focus-visible:ring-destructive',
            className
          )}
          aria-invalid={!!error}
          aria-describedby={error ? `${inputId}-error` : undefined}
        />
        <div className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none">
          {currency}
        </div>
      </div>
      {error && (
        <div id={`${inputId}-error`} role="alert" className="text-destructive text-sm">
          {error}
        </div>
      )}
    </div>
  )
}
