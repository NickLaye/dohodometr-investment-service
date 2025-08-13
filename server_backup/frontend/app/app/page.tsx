'use client'

import { useState, useEffect } from 'react'
import { Plus, TrendingUp, TrendingDown, DollarSign, Target, Calendar, PieChart, BarChart3, Briefcase, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { StatCard } from '@/components/financial/stat-card'
import { PnLIndicator } from '@/components/financial/pnl-indicator'
import { PortfolioCard } from '@/components/financial/portfolio-card'
import { Badge } from '@/components/ui/badge'
import { useQuery } from '@tanstack/react-query'

// Mock data - в реальном приложении это будет API
const mockPortfolios = [
  {
    id: 1,
    name: 'Основной портфель',
    description: 'Долгосрочные инвестиции в акции и облигации',
    totalValue: 2450000,
    dailyChange: 15240,
    dailyChangePercent: 0.8,
    assetsCount: 24,
    isActive: true
  },
  {
    id: 2,
    name: 'Спекулятивный',
    description: 'Краткосрочная торговля и высокорисковые активы',
    totalValue: 850000,
    dailyChange: -8500,
    dailyChangePercent: -1.2,
    assetsCount: 15,
    isActive: true
  },
  {
    id: 3,
    name: 'ИИС',
    description: 'Индивидуальный инвестиционный счет',
    totalValue: 400000,
    dailyChange: 2400,
    dailyChangePercent: 0.6,
    assetsCount: 8,
    isActive: true
  }
]

const mockStats = {
  totalValue: 3700000,
  dailyChange: 9140,
  dailyChangePercent: 0.25,
  weeklyChange: 45200,
  weeklyChangePercent: 1.24,
  monthlyChange: -125000,
  monthlyChangePercent: -3.27,
  portfoliosCount: 3,
  activePositions: 47,
  pendingTransactions: 3
}

const mockTopPerformers = [
  { symbol: 'SBER', name: 'Сбербанк', change: 12.5, changePercent: 4.2 },
  { symbol: 'GAZP', name: 'Газпром', change: 8.9, changePercent: 3.1 },
  { symbol: 'YNDX', name: 'Яндекс', change: 245.0, changePercent: 2.8 }
]

const mockTopLosers = [
  { symbol: 'MAIL', name: 'VK Group', change: -45.2, changePercent: -5.1 },
  { symbol: 'OZON', name: 'Ozon', change: -125.8, changePercent: -4.3 },
  { symbol: 'FIXP', name: 'Fix Price', change: -32.1, changePercent: -3.7 }
]

export default function OverviewPage() {
  const [selectedPeriod, setSelectedPeriod] = useState<'day' | 'week' | 'month'>('day')

  // Mock loading state
  const [isLoading, setIsLoading] = useState(true)
  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 1000)
    return () => clearTimeout(timer)
  }, [])

  const getPeriodData = () => {
    switch (selectedPeriod) {
      case 'week':
        return { change: mockStats.weeklyChange, changePercent: mockStats.weeklyChangePercent }
      case 'month':
        return { change: mockStats.monthlyChange, changePercent: mockStats.monthlyChangePercent }
      default:
        return { change: mockStats.dailyChange, changePercent: mockStats.dailyChangePercent }
    }
  }

  const periodData = getPeriodData()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Обзор портфелей</h1>
          <p className="text-muted-foreground">
            Общая информация о ваших инвестициях и производительности
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button size="sm" variant="outline">
            <BarChart3 className="h-4 w-4 mr-2" />
            Аналитика
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Новый портфель
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Общая стоимость"
          value={mockStats.totalValue}
          currency="₽"
          icon={DollarSign}
          iconColor="text-green-600"
          trend="up"
          description="Все портфели"
        />
        
        <StatCard
          title="Изменение"
          value={Math.abs(periodData.change)}
          changePercent={periodData.changePercent}
          currency="₽"
          icon={periodData.change >= 0 ? TrendingUp : TrendingDown}
          iconColor={periodData.change >= 0 ? "text-green-600" : "text-red-600"}
          trend={periodData.change >= 0 ? "up" : "down"}
          description={`За ${selectedPeriod === 'day' ? 'сегодня' : selectedPeriod === 'week' ? 'неделю' : 'месяц'}`}
        />
        
        <StatCard
          title="Портфели"
          value={mockStats.portfoliosCount}
          icon={Briefcase}
          iconColor="text-blue-600"
          description={`${mockStats.activePositions} активных позиций`}
        />
        
        <StatCard
          title="Ожидают"
          value={mockStats.pendingTransactions}
          icon={Calendar}
          iconColor="text-amber-600"
          description="Отложенные операции"
        />
      </div>

      {/* Period Selector */}
      <div className="flex items-center space-x-2">
        <span className="text-sm font-medium">Период:</span>
        <Tabs value={selectedPeriod} onValueChange={(value) => setSelectedPeriod(value as any)}>
          <TabsList className="grid w-full max-w-md grid-cols-3">
            <TabsTrigger value="day">День</TabsTrigger>
            <TabsTrigger value="week">Неделя</TabsTrigger>
            <TabsTrigger value="month">Месяц</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Portfolios */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Мои портфели</h2>
            <Button variant="outline" size="sm">
              Управление
            </Button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {mockPortfolios.map((portfolio) => (
              <PortfolioCard key={portfolio.id} {...portfolio} />
            ))}
          </div>
        </div>

        {/* Sidebar with performance data */}
        <div className="space-y-6">
          {/* Top Performers */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center">
                <TrendingUp className="h-5 w-5 mr-2 text-green-600" />
                Лидеры роста
              </CardTitle>
              <CardDescription>
                Лучшие активы за сегодня
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {mockTopPerformers.map((item) => (
                <div key={item.symbol} className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{item.symbol}</div>
                    <div className="text-sm text-muted-foreground">{item.name}</div>
                  </div>
                  <PnLIndicator 
                    value={item.change}
                    percentage={item.changePercent}
                    size="sm"
                  />
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Top Losers */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center">
                <TrendingDown className="h-5 w-5 mr-2 text-red-600" />
                Лидеры падения
              </CardTitle>
              <CardDescription>
                Худшие активы за сегодня
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {mockTopLosers.map((item) => (
                <div key={item.symbol} className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{item.symbol}</div>
                    <div className="text-sm text-muted-foreground">{item.name}</div>
                  </div>
                  <PnLIndicator 
                    value={item.change}
                    percentage={item.changePercent}
                    size="sm"
                  />
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Быстрые действия</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-start">
                <Plus className="h-4 w-4 mr-2" />
                Добавить транзакцию
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <PieChart className="h-4 w-4 mr-2" />
                Ребалансировка
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <Target className="h-4 w-4 mr-2" />
                Налоговый расчет
              </Button>
            </CardContent>
          </Card>

          {/* Alerts */}
          <Card className="border-amber-200 dark:border-amber-800">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center text-amber-700 dark:text-amber-400">
                <AlertTriangle className="h-5 w-5 mr-2" />
                Уведомления
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Дивиденды SBER</span>
                  <Badge variant="info">Сегодня</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Экспирация опциона</span>
                  <Badge variant="warning">3 дня</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Налоговая декларация</span>
                  <Badge variant="destructive">Просрочено</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}