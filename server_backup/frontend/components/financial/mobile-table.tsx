'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { PnLIndicator } from '@/components/financial/pnl-indicator'
import { cn } from '@/lib/utils'
import { MoreVertical, TrendingUp, TrendingDown } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

interface MobileTableColumn {
  key: string
  label: string
  render?: (value: any, row: any) => React.ReactNode
  className?: string
  priority?: 'high' | 'medium' | 'low' // For responsive hiding
}

interface MobileTableAction {
  label: string
  onClick: (row: any) => void
  variant?: 'default' | 'destructive'
}

interface MobileTableProps {
  data: any[]
  columns: MobileTableColumn[]
  actions?: MobileTableAction[]
  showDesktopTable?: boolean
  className?: string
  emptyState?: React.ReactNode
}

export function MobileTable({
  data,
  columns,
  actions = [],
  showDesktopTable = true,
  className,
  emptyState
}: MobileTableProps) {
  const highPriorityColumns = columns.filter(col => col.priority === 'high' || !col.priority)
  const mediumPriorityColumns = columns.filter(col => col.priority === 'medium')
  const lowPriorityColumns = columns.filter(col => col.priority === 'low')

  if (data.length === 0) {
    return (
      <div className="text-center py-8">
        {emptyState || (
          <div className="text-muted-foreground">
            Нет данных для отображения
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={className}>
      {/* Mobile Cards - показываем только на мобильных */}
      <div className="md:hidden space-y-3">
        {data.map((row, index) => (
          <Card key={index} className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="space-y-3">
                {/* High Priority Fields - всегда видны */}
                <div className="space-y-2">
                  {highPriorityColumns.map((column) => (
                    <div key={column.key} className="flex justify-between items-start">
                      <span className="text-sm font-medium text-muted-foreground">
                        {column.label}:
                      </span>
                      <div className={cn('text-right', column.className)}>
                        {column.render ? column.render(row[column.key], row) : row[column.key]}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Medium Priority Fields - скрываем на очень маленьких экранах */}
                {mediumPriorityColumns.length > 0 && (
                  <div className="hidden xs:block space-y-2 pt-2 border-t border-border">
                    {mediumPriorityColumns.map((column) => (
                      <div key={column.key} className="flex justify-between items-center">
                        <span className="text-xs text-muted-foreground">
                          {column.label}:
                        </span>
                        <div className={cn('text-xs', column.className)}>
                          {column.render ? column.render(row[column.key], row) : row[column.key]}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Actions */}
                {actions.length > 0 && (
                  <div className="flex justify-end pt-2 border-t border-border">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {actions.map((action, actionIndex) => (
                          <DropdownMenuItem
                            key={actionIndex}
                            onClick={() => action.onClick(row)}
                            className={action.variant === 'destructive' ? 'text-destructive' : ''}
                          >
                            {action.label}
                          </DropdownMenuItem>
                        ))}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Desktop Table - показываем только на десктопе */}
      {showDesktopTable && (
        <div className="hidden md:block">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-border">
                  {columns.map((column) => (
                    <th
                      key={column.key}
                      className={cn(
                        'text-left py-3 px-4 font-medium text-muted-foreground text-sm',
                        column.priority === 'low' && 'hidden xl:table-cell',
                        column.priority === 'medium' && 'hidden lg:table-cell'
                      )}
                    >
                      {column.label}
                    </th>
                  ))}
                  {actions.length > 0 && (
                    <th className="text-right py-3 px-4 font-medium text-muted-foreground text-sm">
                      Действия
                    </th>
                  )}
                </tr>
              </thead>
              <tbody>
                {data.map((row, index) => (
                  <tr
                    key={index}
                    className="border-b border-border hover:bg-muted/50 transition-colors"
                  >
                    {columns.map((column) => (
                      <td
                        key={column.key}
                        className={cn(
                          'py-3 px-4',
                          column.className,
                          column.priority === 'low' && 'hidden xl:table-cell',
                          column.priority === 'medium' && 'hidden lg:table-cell'
                        )}
                      >
                        {column.render ? column.render(row[column.key], row) : row[column.key]}
                      </td>
                    ))}
                    {actions.length > 0 && (
                      <td className="py-3 px-4 text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            {actions.map((action, actionIndex) => (
                              <DropdownMenuItem
                                key={actionIndex}
                                onClick={() => action.onClick(row)}
                                className={action.variant === 'destructive' ? 'text-destructive' : ''}
                              >
                                {action.label}
                              </DropdownMenuItem>
                            ))}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

// Пример использования для транзакций
interface Transaction {
  id: string
  date: string
  symbol: string
  type: 'buy' | 'sell'
  quantity: number
  price: number
  total: number
  commission: number
}

export function TransactionsTable({ transactions }: { transactions: Transaction[] }) {
  const columns: MobileTableColumn[] = [
    {
      key: 'symbol',
      label: 'Актив',
      priority: 'high',
      render: (value, row) => (
        <div>
          <div className="font-medium">{value}</div>
          <div className="text-xs text-muted-foreground">{row.date}</div>
        </div>
      )
    },
    {
      key: 'type',
      label: 'Тип',
      priority: 'high',
      render: (value) => (
        <Badge variant={value === 'buy' ? 'success' : 'destructive'}>
          {value === 'buy' ? 'Покупка' : 'Продажа'}
        </Badge>
      )
    },
    {
      key: 'quantity',
      label: 'Количество',
      priority: 'medium',
      className: 'text-right font-mono'
    },
    {
      key: 'price',
      label: 'Цена',
      priority: 'medium',
      className: 'text-right font-mono',
      render: (value) => `${value.toFixed(2)} ₽`
    },
    {
      key: 'total',
      label: 'Сумма',
      priority: 'high',
      className: 'text-right font-mono',
      render: (value) => `${value.toFixed(2)} ₽`
    },
    {
      key: 'commission',
      label: 'Комиссия',
      priority: 'low',
      className: 'text-right font-mono text-muted-foreground',
      render: (value) => `${value.toFixed(2)} ₽`
    }
  ]

  const actions: MobileTableAction[] = [
    {
      label: 'Просмотр',
      onClick: (row) => console.log('View', row)
    },
    {
      label: 'Редактировать',
      onClick: (row) => console.log('Edit', row)
    },
    {
      label: 'Удалить',
      onClick: (row) => console.log('Delete', row),
      variant: 'destructive'
    }
  ]

  return (
    <MobileTable
      data={transactions}
      columns={columns}
      actions={actions}
      emptyState={
        <div className="text-center py-8">
          <TrendingUp className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">Нет транзакций</h3>
          <p className="text-muted-foreground">
            Добавьте первую транзакцию, чтобы начать отслеживание
          </p>
        </div>
      }
    />
  )
}

// Пример использования для портфелей
interface Position {
  symbol: string
  name: string
  quantity: number
  avgPrice: number
  currentPrice: number
  value: number
  pnl: number
  pnlPercent: number
  weight: number
}

export function PositionsTable({ positions }: { positions: Position[] }) {
  const columns: MobileTableColumn[] = [
    {
      key: 'symbol',
      label: 'Актив',
      priority: 'high',
      render: (value, row) => (
        <div>
          <div className="font-medium">{value}</div>
          <div className="text-xs text-muted-foreground">{row.name}</div>
        </div>
      )
    },
    {
      key: 'quantity',
      label: 'Кол-во',
      priority: 'medium',
      className: 'text-right font-mono'
    },
    {
      key: 'currentPrice',
      label: 'Цена',
      priority: 'medium',
      className: 'text-right font-mono',
      render: (value) => `${value.toFixed(2)} ₽`
    },
    {
      key: 'value',
      label: 'Стоимость',
      priority: 'high',
      className: 'text-right font-mono',
      render: (value) => `${value.toFixed(0)} ₽`
    },
    {
      key: 'pnl',
      label: 'P&L',
      priority: 'high',
      className: 'text-right',
      render: (value, row) => (
        <PnLIndicator
          value={value}
          percentage={row.pnlPercent}
          size="sm"
        />
      )
    },
    {
      key: 'weight',
      label: 'Доля',
      priority: 'low',
      className: 'text-right',
      render: (value) => `${value.toFixed(1)}%`
    }
  ]

  return (
    <MobileTable
      data={positions}
      columns={columns}
      emptyState={
        <div className="text-center py-8">
          <TrendingDown className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">Нет позиций</h3>
          <p className="text-muted-foreground">
            Добавьте инструменты в портфель для отслеживания
          </p>
        </div>
      }
    />
  )
}
