'use client'

import { Card, CardContent } from '@/components/ui/card'
import { PnLIndicator } from '@/components/financial/pnl-indicator'
import { cn } from '@/lib/utils'
import { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  change?: number
  changePercent?: number
  icon?: LucideIcon
  iconColor?: string
  currency?: string
  description?: string
  className?: string
  trend?: 'up' | 'down' | 'neutral'
}

export function StatCard({
  title,
  value,
  change,
  changePercent,
  icon: Icon,
  iconColor = 'text-primary',
  currency,
  description,
  className,
  trend
}: StatCardProps) {
  const formatValue = (val: string | number) => {
    if (typeof val === 'number') {
      return new Intl.NumberFormat('ru-RU', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
      }).format(val)
    }
    return val
  }

  const getTrendColor = () => {
    switch (trend) {
      case 'up': return 'border-l-green-500'
      case 'down': return 'border-l-red-500'
      default: return 'border-l-primary'
    }
  }

  return (
    <Card className={cn(
      'relative overflow-hidden transition-all duration-200 hover:shadow-md border-l-4',
      getTrendColor(),
      className
    )}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1 flex-1">
            <p className="text-sm font-medium text-muted-foreground">
              {title}
            </p>
            <div className="flex items-baseline space-x-2">
              <p className="text-2xl font-bold font-mono tabular-nums">
                {formatValue(value)}
                {currency && <span className="text-lg ml-1">{currency}</span>}
              </p>
            </div>
            {description && (
              <p className="text-xs text-muted-foreground">
                {description}
              </p>
            )}
          </div>
          
          {Icon && (
            <div className={cn('p-3 rounded-full bg-muted/50', iconColor)}>
              <Icon className="h-6 w-6" />
            </div>
          )}
        </div>
        
        {(change !== undefined || changePercent !== undefined) && (
          <div className="mt-4 flex items-center">
            <PnLIndicator
              value={change || 0}
              percentage={changePercent}
              currency={currency}
              size="sm"
              showSign={true}
            />
            <span className="ml-2 text-xs text-muted-foreground">
              за сегодня
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
