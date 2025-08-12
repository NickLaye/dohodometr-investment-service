'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { PnLIndicator } from '@/components/financial/pnl-indicator'
import { Briefcase, TrendingUp, MoreVertical, Eye, Edit, Trash } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import Link from 'next/link'

interface PortfolioCardProps {
  id: number
  name: string
  description?: string
  totalValue: number
  dailyChange: number
  dailyChangePercent: number
  assetsCount: number
  currency?: string
  isActive?: boolean
  className?: string
  onEdit?: () => void
  onDelete?: () => void
}

export function PortfolioCard({
  id,
  name,
  description,
  totalValue,
  dailyChange,
  dailyChangePercent,
  assetsCount,
  currency = '₽',
  isActive = true,
  className,
  onEdit,
  onDelete
}: PortfolioCardProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  return (
    <Card className={cn(
      'relative group hover:shadow-lg transition-all duration-200 hover:-translate-y-1',
      !isActive && 'opacity-75 bg-muted/50',
      className
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className={cn(
              'p-2 rounded-lg',
              isActive ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'
            )}>
              <Briefcase className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-lg font-semibold">
                <Link 
                  href={`/app/portfolios/${id}`}
                  className="hover:text-primary transition-colors"
                >
                  {name}
                </Link>
              </CardTitle>
              {description && (
                <CardDescription className="mt-1">
                  {description}
                </CardDescription>
              )}
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {!isActive && (
              <Badge variant="secondary" className="text-xs">
                Неактивный
              </Badge>
            )}
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="icon"
                  className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                  aria-label={`Действия для портфеля ${name}`}
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem asChild>
                  <Link href={`/app/portfolios/${id}`} className="flex items-center">
                    <Eye className="mr-2 h-4 w-4" />
                    Просмотр
                  </Link>
                </DropdownMenuItem>
                {onEdit && (
                  <DropdownMenuItem onClick={onEdit}>
                    <Edit className="mr-2 h-4 w-4" />
                    Редактировать
                  </DropdownMenuItem>
                )}
                <DropdownMenuSeparator />
                {onDelete && (
                  <DropdownMenuItem 
                    onClick={onDelete}
                    className="text-destructive focus:text-destructive"
                  >
                    <Trash className="mr-2 h-4 w-4" />
                    Удалить
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        <div className="space-y-4">
          {/* Total Value */}
          <div>
            <div className="text-2xl font-bold font-mono tabular-nums">
              {formatCurrency(totalValue)} {currency}
            </div>
            <div className="text-sm text-muted-foreground">
              Общая стоимость
            </div>
          </div>
          
          {/* Daily Change */}
          <div className="flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              Изменение за день:
            </div>
            <PnLIndicator 
              value={dailyChange}
              percentage={dailyChangePercent}
              currency={currency}
              size="sm"
            />
          </div>
          
          {/* Assets Count */}
          <div className="flex items-center justify-between pt-2 border-t">
            <div className="text-sm text-muted-foreground">
              Активов в портфеле:
            </div>
            <div className="flex items-center space-x-1 text-sm font-medium">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              <span>{assetsCount}</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
