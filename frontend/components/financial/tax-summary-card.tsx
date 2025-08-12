'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { PnLIndicator } from '@/components/financial/pnl-indicator'
import { FileText, Calculator, TrendingDown, Info, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TaxSummaryData {
  totalIncome: number
  totalExpenses: number
  taxableIncome: number
  ndflAmount: number
  ndflRate: number
  ldvExemption: number
  iisDeduction: number
  stockPnl: number
  dividendIncome: number
  recommendations: string[]
  iisOptimalStrategy?: 'A' | 'B'
  iisAdvantageAmount?: number
}

interface TaxSummaryCardProps {
  data: TaxSummaryData
  year: number
  className?: string
  onGenerateReport?: () => void
  onOptimize?: () => void
}

export function TaxSummaryCard({
  data,
  year,
  className,
  onGenerateReport,
  onOptimize
}: TaxSummaryCardProps) {
  const totalSavings = data.ldvExemption + data.iisDeduction
  const effectiveRate = data.taxableIncome > 0 ? (data.ndflAmount / data.taxableIncome) * 100 : 0
  
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Calculator className="h-6 w-6 text-primary" />
            </div>
            <div>
              <CardTitle className="text-xl">Налоговый расчет {year}</CardTitle>
              <CardDescription>
                НДФЛ по инвестиционным операциям
              </CardDescription>
            </div>
          </div>
          <Badge variant={data.ndflAmount > 0 ? 'destructive' : 'success'}>
            {data.ndflAmount > 0 ? 'К доплате' : 'Льготы'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6 p-6">
        {/* Основные показатели */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-muted/50 rounded-lg">
            <div className="text-2xl font-bold font-mono">
              {formatCurrency(data.totalIncome)} ₽
            </div>
            <div className="text-sm text-muted-foreground mt-1">
              Общий доход
            </div>
          </div>
          
          <div className="text-center p-4 bg-muted/50 rounded-lg">
            <div className="text-2xl font-bold font-mono">
              {formatCurrency(data.taxableIncome)} ₽
            </div>
            <div className="text-sm text-muted-foreground mt-1">
              Налогооблагаемый доход
            </div>
          </div>
          
          <div className="text-center p-4 bg-gradient-to-r from-red-50 to-orange-50 dark:from-red-950/20 dark:to-orange-950/20 rounded-lg">
            <div className={cn(
              'text-2xl font-bold font-mono',
              data.ndflAmount > 0 ? 'text-red-600' : 'text-green-600'
            )}>
              {formatCurrency(data.ndflAmount)} ₽
            </div>
            <div className="text-sm text-muted-foreground mt-1">
              НДФЛ к доплате
            </div>
          </div>
        </div>

        {/* Детализация по типам доходов */}
        <div className="space-y-3">
          <h4 className="font-medium flex items-center">
            <TrendingDown className="h-4 w-4 mr-2" />
            Детализация доходов
          </h4>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Торговые операции:</span>
              <PnLIndicator value={data.stockPnl} size="sm" />
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Дивиденды:</span>
              <span className="font-mono">{formatCurrency(data.dividendIncome)} ₽</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Расходы:</span>
              <span className="font-mono text-muted-foreground">
                -{formatCurrency(data.totalExpenses)} ₽
              </span>
            </div>
          </div>
        </div>

        {/* Льготы и экономия */}
        {totalSavings > 0 && (
          <div className="space-y-3">
            <h4 className="font-medium flex items-center">
              <Info className="h-4 w-4 mr-2 text-green-600" />
              Применены льготы
            </h4>
            <div className="bg-green-50 dark:bg-green-950/20 p-4 rounded-lg space-y-2">
              {data.ldvExemption > 0 && (
                <div className="flex justify-between items-center">
                  <span className="text-sm">ЛДВ (длительное владение):</span>
                  <span className="font-mono text-green-600">
                    -{formatCurrency(data.ldvExemption)} ₽
                  </span>
                </div>
              )}
              {data.iisDeduction > 0 && (
                <div className="flex justify-between items-center">
                  <span className="text-sm">ИИС {data.iisOptimalStrategy ? `тип ${data.iisOptimalStrategy}` : ''}:</span>
                  <span className="font-mono text-green-600">
                    -{formatCurrency(data.iisDeduction)} ₽
                  </span>
                </div>
              )}
              <div className="pt-2 border-t border-green-200 dark:border-green-800 flex justify-between items-center font-medium">
                <span>Общая экономия:</span>
                <span className="text-green-600 font-mono">
                  -{formatCurrency(totalSavings)} ₽
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Эффективная ставка */}
        <div className="p-4 bg-muted/50 rounded-lg">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Эффективная налоговая ставка:</span>
            <span className="font-mono text-lg">
              {effectiveRate.toFixed(1)}%
            </span>
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            Фактическая ставка с учетом всех льгот
          </div>
        </div>

        {/* Рекомендации */}
        {data.recommendations.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-medium flex items-center">
              <AlertTriangle className="h-4 w-4 mr-2 text-amber-600" />
              Рекомендации по оптимизации
            </h4>
            <div className="space-y-2">
              {data.recommendations.map((recommendation, index) => (
                <div key={index} className="flex items-start space-x-2 text-sm">
                  <div className="w-1.5 h-1.5 bg-amber-500 rounded-full mt-2 flex-shrink-0" />
                  <span>{recommendation}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ИИС стратегия */}
        {data.iisOptimalStrategy && data.iisAdvantageAmount && (
          <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-blue-900 dark:text-blue-300">
                Оптимальная стратегия ИИС
              </span>
              <Badge variant="info">Тип {data.iisOptimalStrategy}</Badge>
            </div>
            <div className="text-sm text-blue-700 dark:text-blue-400">
              Дополнительная экономия: {formatCurrency(data.iisAdvantageAmount)} ₽
            </div>
          </div>
        )}

        {/* Действия */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t">
          {onGenerateReport && (
            <Button onClick={onGenerateReport} className="flex items-center">
              <FileText className="h-4 w-4 mr-2" />
              Сформировать отчет
            </Button>
          )}
          {onOptimize && (
            <Button variant="outline" onClick={onOptimize} className="flex items-center">
              <Calculator className="h-4 w-4 mr-2" />
              Оптимизировать
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
