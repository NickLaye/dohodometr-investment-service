'use client'

import { useState, useEffect } from 'react'
import { Calculator, TrendingUp, Shield, DollarSign, Calendar, Info, CheckCircle, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface TaxCalculationResult {
  total_income: number
  total_expenses: number
  taxable_income: number
  ndfl_amount: number
  ndfl_rate: number
  ldv_exemption: number
  iis_deduction: number
  stock_pnl: number
  dividend_income: number
  recommendations: string[]
}

interface IISStrategyResult {
  type_a_net_result: number
  type_b_net_result: number
  optimal_strategy: string
  advantage_amount: number
}

export default function TaxDemoPage() {
  const [demoResult, setDemoResult] = useState<TaxCalculationResult | null>(null)
  const [iisResult, setIISResult] = useState<IISStrategyResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [iisParams, setIISParams] = useState({
    annual_income: 2000000,
    expected_return: 10,
    investment_horizon: 5,
    annual_contribution: 400000
  })

  // Загружаем демо-расчет при загрузке страницы
  useEffect(() => {
    loadDemoCalculation()
  }, [])

  const loadDemoCalculation = async () => {
    try {
      setLoading(true)
      // Используем централизованный API клиент
      const { api } = await import('@/lib/api-client')
      const response = await api.tax.demoCalculation()
      setDemoResult(response.data.tax_calculation)
    } catch (error) {
      console.error('Ошибка загрузки демо-расчета:', error)
    } finally {
      setLoading(false)
    }
  }

  const calculateIISStrategy = async () => {
    try {
      setLoading(true)
      // Используем централизованный API клиент
      const { api } = await import('@/lib/api-client')
      const response = await api.tax.iisStrategy(iisParams)
      setIISResult(response.data)
    } catch (error) {
      console.error('Ошибка расчета стратегии ИИС:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatRubles = (amount: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <div className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-2 rounded-lg">
                <Calculator className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Налоговый Калькулятор РФ</h1>
                <p className="text-sm text-gray-600">Демонстрация возможностей Dohodometr.ru</p>
              </div>
            </div>
            <Button
              onClick={() => window.open('https://dohodometr.ru', '_blank')}
              className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
            >
              Перейти на сайт
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 space-y-8">
        {/* Hero Section */}
        <div className="text-center space-y-4">
          <h2 className="text-3xl font-bold text-gray-900">
            Автоматический расчет налогов с инвестиций
          </h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Первый российский сервис с полным соответствием НК РФ. 
            Рассчитываем НДФЛ, ИИС, ЛДВ и все налоговые льготы автоматически.
          </p>
        </div>

        {/* Key Features */}
        <div className="grid md:grid-cols-3 gap-6">
          <Card className="border-0 shadow-lg bg-gradient-to-br from-green-50 to-emerald-50">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Shield className="h-5 w-5 text-green-600" />
                <CardTitle className="text-green-800">100% Compliance</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-green-700">
                Полное соответствие НК РФ, ФЗ-152 и всему российскому законодательству
              </p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-gradient-to-br from-blue-50 to-cyan-50">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <TrendingUp className="h-5 w-5 text-blue-600" />
                <CardTitle className="text-blue-800">Умная аналитика</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-blue-700">
                FIFO учет, автоматическое применение льгот ИИС и ЛДВ
              </p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-gradient-to-br from-purple-50 to-violet-50">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <DollarSign className="h-5 w-5 text-purple-600" />
                <CardTitle className="text-purple-800">Экономия налогов</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-purple-700">
                Персональные рекомендации для минимизации налоговых обязательств
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Demo Calculation Results */}
        {demoResult && (
          <Card className="shadow-xl border-0">
            <CardHeader className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-lg">
              <CardTitle className="flex items-center space-x-2">
                <Calculator className="h-5 w-5" />
                <span>Демонстрационный расчет налогов</span>
              </CardTitle>
              <CardDescription className="text-blue-100">
                Пример расчета для типичного частного инвестора с акциями и дивидендами
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {formatRubles(demoResult.total_income)}
                  </div>
                  <div className="text-sm text-gray-600">Общий доход</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {formatRubles(demoResult.stock_pnl)}
                  </div>
                  <div className="text-sm text-gray-600">Прибыль от акций</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {formatRubles(demoResult.dividend_income)}
                  </div>
                  <div className="text-sm text-gray-600">Дивиденды</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {formatRubles(demoResult.ndfl_amount)}
                  </div>
                  <div className="text-sm text-gray-600">НДФЛ к доплате</div>
                </div>
              </div>

              <div className="mt-6 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <h4 className="font-semibold text-yellow-800 mb-2 flex items-center">
                  <Info className="h-4 w-4 mr-2" />
                  Рекомендации по оптимизации
                </h4>
                <ul className="space-y-1">
                  {demoResult.recommendations.map((rec, index) => (
                    <li key={index} className="text-sm text-yellow-700 flex items-start">
                      <CheckCircle className="h-4 w-4 mt-0.5 mr-2 flex-shrink-0" />
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>
        )}

        {/* IIS Strategy Calculator */}
        <Card className="shadow-xl border-0">
          <CardHeader className="bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-t-lg">
            <CardTitle>Калькулятор оптимальной стратегии ИИС</CardTitle>
            <CardDescription className="text-purple-100">
              Сравните эффективность ИИС типа А и Б для ваших параметров
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <Label htmlFor="income">Годовой доход (руб)</Label>
                  <Input
                    id="income"
                    type="number"
                    value={iisParams.annual_income}
                    onChange={(e) => setIISParams({
                      ...iisParams,
                      annual_income: Number(e.target.value)
                    })}
                    className="mt-1"
                  />
                </div>
                
                <div>
                  <Label htmlFor="return">Ожидаемая доходность (%)</Label>
                  <Input
                    id="return"
                    type="number"
                    value={iisParams.expected_return}
                    onChange={(e) => setIISParams({
                      ...iisParams,
                      expected_return: Number(e.target.value)
                    })}
                    className="mt-1"
                  />
                </div>
                
                <div>
                  <Label htmlFor="horizon">Горизонт инвестирования (лет)</Label>
                  <Input
                    id="horizon"
                    type="number"
                    value={iisParams.investment_horizon}
                    onChange={(e) => setIISParams({
                      ...iisParams,
                      investment_horizon: Number(e.target.value)
                    })}
                    className="mt-1"
                  />
                </div>
                
                <div>
                  <Label htmlFor="contribution">Годовой взнос (руб)</Label>
                  <Input
                    id="contribution"
                    type="number"
                    value={iisParams.annual_contribution}
                    onChange={(e) => setIISParams({
                      ...iisParams,
                      annual_contribution: Number(e.target.value)
                    })}
                    className="mt-1"
                  />
                </div>
                
                <Button 
                  onClick={calculateIISStrategy}
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                >
                  {loading ? 'Рассчитываем...' : 'Рассчитать стратегию'}
                </Button>
              </div>

              {iisResult && (
                <div className="space-y-4">
                  <h4 className="font-semibold text-gray-900">Результаты сравнения:</h4>
                  
                  <div className="space-y-3">
                    <div className={`p-4 rounded-lg border-2 ${
                      iisResult.optimal_strategy === 'A' 
                        ? 'bg-green-50 border-green-200' 
                        : 'bg-gray-50 border-gray-200'
                    }`}>
                      <div className="flex items-center justify-between">
                        <span className="font-medium">ИИС тип А (вычет на взносы)</span>
                        {iisResult.optimal_strategy === 'A' && (
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        )}
                      </div>
                      <div className="text-lg font-bold text-gray-900">
                        {formatRubles(iisResult.type_a_net_result)}
                      </div>
                    </div>
                    
                    <div className={`p-4 rounded-lg border-2 ${
                      iisResult.optimal_strategy === 'B' 
                        ? 'bg-green-50 border-green-200' 
                        : 'bg-gray-50 border-gray-200'
                    }`}>
                      <div className="flex items-center justify-between">
                        <span className="font-medium">ИИС тип Б (освобождение доходов)</span>
                        {iisResult.optimal_strategy === 'B' && (
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        )}
                      </div>
                      <div className="text-lg font-bold text-gray-900">
                        {formatRubles(iisResult.type_b_net_result)}
                      </div>
                    </div>
                  </div>
                  
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <div className="font-medium text-blue-800">
                      Преимущество ИИС тип {iisResult.optimal_strategy}:
                    </div>
                    <div className="text-xl font-bold text-blue-900">
                      {formatRubles(iisResult.advantage_amount)}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Important Dates */}
        <Card className="shadow-lg border-0">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Calendar className="h-5 w-5" />
              <span>Важные налоговые даты 2024</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <AlertCircle className="h-5 w-5 text-orange-500" />
                  <div>
                    <div className="font-medium">31 марта 2025</div>
                    <div className="text-sm text-gray-600">Срок подачи декларации за 2024 год</div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <AlertCircle className="h-5 w-5 text-red-500" />
                  <div>
                    <div className="font-medium">15 июля 2025</div>
                    <div className="text-sm text-gray-600">Срок доплаты НДФЛ за 2024 год</div>
                  </div>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <div>
                    <div className="font-medium">31 декабря 2024</div>
                    <div className="text-sm text-gray-600">Последний день для взноса на ИИС</div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <Info className="h-5 w-5 text-blue-500" />
                  <div>
                    <div className="font-medium">3 года владения</div>
                    <div className="text-sm text-gray-600">Минимальный срок для льготы ЛДВ</div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* CTA Section */}
        <Card className="shadow-xl border-0 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white">
          <CardContent className="p-8 text-center">
            <h3 className="text-2xl font-bold mb-4">
              Готовы оптимизировать ваши налоги?
            </h3>
            <p className="text-lg mb-6 text-indigo-100">
              Dohodometr.ru - первый российский сервис с автоматическим расчетом всех налогов и льгот
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                size="lg"
                variant="secondary"
                className="bg-white text-indigo-600 hover:bg-gray-100"
                onClick={() => window.open('https://dohodometr.ru', '_blank')}
              >
                Перейти на сайт
              </Button>
              <Button 
                size="lg"
                variant="outline"
                className="border-white text-white hover:bg-white/10"
                onClick={() => loadDemoCalculation()}
              >
                Обновить демо
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
