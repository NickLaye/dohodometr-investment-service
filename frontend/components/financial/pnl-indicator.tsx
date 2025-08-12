'use client'

import { cn } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface PnLIndicatorProps {
  value: number
  percentage?: number
  showArrow?: boolean
  showSign?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
  currency?: string
}

export function PnLIndicator({
  value,
  percentage,
  showArrow = true,
  showSign = true,
  size = 'md',
  className,
  currency = '₽'
}: PnLIndicatorProps) {
  const isPositive = value > 0
  const isNegative = value < 0
  const isNeutral = value === 0

  const formatValue = (val: number) => {
    return new Intl.NumberFormat('ru-RU', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(Math.abs(val))
  }

  const formatPercentage = (val: number) => {
    return new Intl.NumberFormat('ru-RU', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 2,
    }).format(Math.abs(val))
  }

  const sizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg font-medium'
  }

  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4', 
    lg: 'h-5 w-5'
  }

  const getColorClasses = () => {
    if (isPositive) return 'text-green-600 dark:text-green-400'
    if (isNegative) return 'text-red-600 dark:text-red-400'
    return 'text-muted-foreground'
  }

  const getIcon = () => {
    if (isPositive) return <TrendingUp className={iconSizes[size]} />
    if (isNegative) return <TrendingDown className={iconSizes[size]} />
    return <Minus className={iconSizes[size]} />
  }

  return (
    <div 
      className={cn(
        'inline-flex items-center gap-1 font-mono tabular-nums',
        sizeClasses[size],
        getColorClasses(),
        className
      )}
      title={`${showSign && !isNeutral ? (isPositive ? '+' : '−') : ''}${formatValue(value)} ${currency}${percentage ? ` (${isPositive ? '+' : '−'}${formatPercentage(percentage)}%)` : ''}`}
    >
      {showArrow && getIcon()}
      <span>
        {showSign && !isNeutral && (isPositive ? '+' : '−')}
        {formatValue(value)} {currency}
      </span>
      {percentage !== undefined && (
        <span className="opacity-75">
          ({showSign && !isNeutral && (isPositive ? '+' : '−')}{formatPercentage(percentage)}%)
        </span>
      )}
    </div>
  )
}
