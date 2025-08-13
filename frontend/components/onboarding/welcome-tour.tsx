'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { ArrowRight, ArrowLeft, Sparkles, Target, PieChart, TrendingUp, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface WelcomeTourProps {
  isOpen: boolean
  onClose: () => void
  onComplete: () => void
}

const tourSteps = [
  {
    id: 'welcome',
    title: 'Добро пожаловать в Dohodometr!',
    description: 'Давайте познакомим вас с основными возможностями сервиса учета инвестиций',
    icon: Sparkles,
    content: (
      <div className="space-y-4">
        <div className="text-center">
          <div className="mx-auto w-24 h-24 bg-primary/10 rounded-full flex items-center justify-center mb-4">
            <Sparkles className="h-12 w-12 text-primary" />
          </div>
          <h3 className="text-lg font-semibold mb-2">Начнем знакомство!</h3>
          <p className="text-muted-foreground">
            За несколько минут вы узнаете, как эффективно управлять своими инвестициями
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-6">
          <div className="text-center p-3 rounded-lg bg-muted/50">
            <Target className="h-6 w-6 text-primary mx-auto mb-2" />
            <div className="text-sm font-medium">Портфели</div>
          </div>
          <div className="text-center p-3 rounded-lg bg-muted/50">
            <PieChart className="h-6 w-6 text-primary mx-auto mb-2" />
            <div className="text-sm font-medium">Аналитика</div>
          </div>
          <div className="text-center p-3 rounded-lg bg-muted/50">
            <TrendingUp className="h-6 w-6 text-primary mx-auto mb-2" />
            <div className="text-sm font-medium">Налоги</div>
          </div>
        </div>
      </div>
    )
  },
  {
    id: 'portfolios',
    title: 'Создание портфелей',
    description: 'Организуйте свои инвестиции по целям и стратегиям',
    icon: Target,
    content: (
      <div className="space-y-4">
        <div className="p-4 bg-muted/50 rounded-lg">
          <h4 className="font-medium mb-2">Типы портфелей:</h4>
          <ul className="space-y-2 text-sm">
            <li className="flex items-center">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2" />
              Долгосрочные инвестиции
            </li>
            <li className="flex items-center">
              <div className="w-2 h-2 bg-blue-500 rounded-full mr-2" />
              Спекулятивная торговля
            </li>
            <li className="flex items-center">
              <div className="w-2 h-2 bg-purple-500 rounded-full mr-2" />
              ИИС (льготное налогообложение)
            </li>
          </ul>
        </div>
        <p className="text-sm text-muted-foreground">
          Каждый портфель отслеживается отдельно с собственной статистикой и отчетами
        </p>
      </div>
    )
  },
  {
    id: 'analytics',
    title: 'Аналитика и отчеты',
    description: 'Анализируйте доходность и оптимизируйте стратегию',
    icon: PieChart,
    content: (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-green-50 dark:bg-green-950/20 rounded-lg">
            <div className="text-lg font-bold text-green-600">+12.5%</div>
            <div className="text-xs text-muted-foreground">Доходность</div>
          </div>
          <div className="p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
            <div className="text-lg font-bold text-blue-600">1.2</div>
            <div className="text-xs text-muted-foreground">Sharpe Ratio</div>
          </div>
        </div>
        <div className="space-y-2">
          <h4 className="font-medium">Доступные метрики:</h4>
          <ul className="text-sm space-y-1 text-muted-foreground">
            <li>• Time-Weighted Return (TWR)</li>
            <li>• Extended Internal Rate of Return (XIRR)</li>
            <li>• Сравнение с бенчмарками (IMOEX, S&P 500)</li>
            <li>• Анализ волатильности и рисков</li>
          </ul>
        </div>
      </div>
    )
  },
  {
    id: 'taxes',
    title: 'Налоговый калькулятор РФ',
    description: 'Автоматический расчет НДФЛ с учетом всех льгот',
    icon: TrendingUp,
    content: (
      <div className="space-y-4">
        <div className="p-4 bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-950/20 dark:to-blue-950/20 rounded-lg">
          <h4 className="font-medium mb-2 flex items-center">
            <span className="w-6 h-6 bg-green-100 dark:bg-green-800 rounded mr-2 flex items-center justify-center text-xs">₽</span>
            Экономия на налогах
          </h4>
          <div className="text-2xl font-bold text-green-600">52,000 ₽</div>
          <div className="text-sm text-muted-foreground">за счет льгот ИИС и ЛДВ</div>
        </div>
        <div className="space-y-2">
          <h4 className="font-medium">Поддерживаемые льготы:</h4>
          <ul className="text-sm space-y-1">
            <li className="flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-2" />
              ИИС типа А (вычет на взнос)
            </li>
            <li className="flex items-center">
              <span className="w-2 h-2 bg-blue-500 rounded-full mr-2" />
              ИИС типа Б (освобождение от НДФЛ)
            </li>
            <li className="flex items-center">
              <span className="w-2 h-2 bg-purple-500 rounded-full mr-2" />
              ЛДВ (длительное владение 3+ года)
            </li>
          </ul>
        </div>
      </div>
    )
  },
  {
    id: 'complete',
    title: 'Все готово!',
    description: 'Начните добавлять свои инвестиции и отслеживайте результаты',
    icon: Sparkles,
    content: (
      <div className="space-y-4 text-center">
        <div className="mx-auto w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
          <Sparkles className="h-8 w-8 text-green-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold mb-2">Поздравляем!</h3>
          <p className="text-muted-foreground">
            Теперь вы знакомы с основными возможностями Dohodometr
          </p>
        </div>
        <div className="p-4 bg-primary/5 rounded-lg">
          <h4 className="font-medium mb-2">Следующие шаги:</h4>
          <ol className="text-sm space-y-1 text-left">
            <li>1. Создайте свой первый портфель</li>
            <li>2. Импортируйте данные от брокера</li>
            <li>3. Настройте уведомления</li>
            <li>4. Изучите налоговые отчеты</li>
          </ol>
        </div>
      </div>
    )
  }
]

export function WelcomeTour({ isOpen, onClose, onComplete }: WelcomeTourProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setIsVisible(true)
    }
  }, [isOpen])

  const handleClose = () => {
    setIsVisible(false)
    setTimeout(() => {
      onClose()
      setCurrentStep(0)
    }, 200)
  }

  const handleNext = () => {
    if (currentStep < tourSteps.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleComplete = () => {
    onComplete()
    handleClose()
  }

  const currentStepData = tourSteps[currentStep]
  const progress = ((currentStep + 1) / tourSteps.length) * 100

  if (!isOpen || !currentStepData) return null

  return (
    <div className="fixed inset-0 bg-background/95 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card 
        className={cn(
          'w-full max-w-2xl mx-auto transition-all duration-200',
          isVisible ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
        )}
      >
        <CardHeader className="relative">
          <Button
            variant="ghost"
            size="icon"
            onClick={handleClose}
            className="absolute right-2 top-2 h-8 w-8"
            aria-label="Пропустить знакомство"
          >
            <X className="h-4 w-4" />
          </Button>
          
          <div className="space-y-2">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <currentStepData.icon className="h-6 w-6 text-primary" />
              </div>
              <div>
                <CardTitle className="text-xl">{currentStepData.title}</CardTitle>
                <CardDescription>{currentStepData.description}</CardDescription>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>Шаг {currentStep + 1} из {tourSteps.length}</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {currentStepData.content}
          
          <div className="flex items-center justify-between pt-4">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={currentStep === 0}
              className="flex items-center"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Назад
            </Button>
            
            <div className="flex space-x-2">
              <Button variant="ghost" onClick={handleClose}>
                Пропустить
              </Button>
              
              {currentStep === tourSteps.length - 1 ? (
                <Button onClick={handleComplete} className="flex items-center">
                  Начать работу
                  <Sparkles className="h-4 w-4 ml-2" />
                </Button>
              ) : (
                <Button onClick={handleNext} className="flex items-center">
                  Далее
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
