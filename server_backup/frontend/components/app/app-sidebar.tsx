'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  BarChart3,
  Briefcase,
  Calendar,
  FileText,
  Home,
  PieChart,
  Settings,
  Target,
  TrendingUp,
  Upload,
  Wallet,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'

const navigation = [
  {
    name: 'Обзор',
    href: '/app',
    icon: Home,
    description: 'Общий обзор портфелей'
  },
  {
    name: 'Портфели',
    href: '/app/portfolios',
    icon: Briefcase,
    description: 'Управление портфелями'
  },
  {
    name: 'Транзакции',
    href: '/app/transactions',
    icon: Wallet,
    description: 'История операций'
  },
  {
    name: 'Аналитика',
    href: '/app/analytics',
    icon: BarChart3,
    description: 'Анализ производительности',
    children: [
      {
        name: 'Производительность',
        href: '/app/analytics/performance',
        icon: TrendingUp,
      },
      {
        name: 'Распределение',
        href: '/app/analytics/allocation',
        icon: PieChart,
      },
      {
        name: 'Риск-анализ',
        href: '/app/analytics/risk',
        icon: Target,
      },
    ],
  },
  {
    name: 'Налоги',
    href: '/app/taxes',
    icon: FileText,
    description: 'Расчет налогов РФ'
  },
  {
    name: 'Планирование',
    href: '/app/planning',
    icon: Calendar,
    description: 'Цели и планы'
  },
  {
    name: 'Импорт',
    href: '/app/import',
    icon: Upload,
    description: 'Импорт от брокеров'
  },
]

const bottomNavigation = [
  {
    name: 'Настройки',
    href: '/app/settings',
    icon: Settings,
    description: 'Персональные настройки'
  },
]

interface NavItemProps {
  item: {
    name: string
    href: string
    icon: any
    description?: string
    children?: {
      name: string
      href: string
      icon: any
    }[]
  }
  isCollapsed: boolean
  isActive: boolean
}

function NavItem({ item, isCollapsed, isActive }: NavItemProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const pathname = usePathname()

  const hasChildren = item.children && item.children.length > 0
  const isChildActive = hasChildren && item.children.some(child => pathname === child.href)

  const navContent = (
    <div className="space-y-1">
      {hasChildren && !isCollapsed ? (
        <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
          <CollapsibleTrigger asChild>
            <Button
              variant="ghost"
              className={cn(
                'w-full justify-start space-x-3 px-3 py-2 h-auto font-medium transition-colors',
                isActive || isChildActive
                  ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent'
              )}
              aria-expanded={isExpanded}
              aria-label={`${item.name}${hasChildren ? ', развернуть подменю' : ''}`}
            >
              <item.icon className="h-4 w-4 flex-shrink-0" />
              <span className="flex-1 text-left">{item.name}</span>
              <ChevronRight
                className={cn(
                  'h-4 w-4 transition-transform',
                  isExpanded && 'rotate-90'
                )}
              />
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent className="ml-6 space-y-1 mt-1">
            {item.children!.map((child) => (
              <Link
                key={child.name}
                href={child.href}
                className={cn(
                  'flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                  pathname === child.href
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                )}
                aria-label={child.name}
              >
                <child.icon className="h-4 w-4 flex-shrink-0" />
                <span>{child.name}</span>
              </Link>
            ))}
          </CollapsibleContent>
        </Collapsible>
      ) : (
        <Link
          href={item.href}
          className={cn(
            'flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
            isActive || isChildActive
              ? 'bg-primary text-primary-foreground hover:bg-primary/90'
              : 'text-muted-foreground hover:text-foreground hover:bg-accent',
            isCollapsed && 'justify-center'
          )}
          aria-label={isCollapsed ? `${item.name}${item.description ? ': ' + item.description : ''}` : item.name}
        >
          <item.icon className="h-4 w-4 flex-shrink-0" />
          {!isCollapsed && <span className="flex-1">{item.name}</span>}
        </Link>
      )}
    </div>
  )

  // Wrap with tooltip when collapsed
  if (isCollapsed) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          {navContent}
        </TooltipTrigger>
        <TooltipContent side="right" className="font-medium">
          <div>
            <div>{item.name}</div>
            {item.description && (
              <div className="text-xs text-muted-foreground mt-1">{item.description}</div>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    )
  }

  return navContent
}

export function AppSidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const pathname = usePathname()

  return (
    <TooltipProvider>
      <div
        className={cn(
          'relative hidden md:flex flex-col bg-background border-r border-border transition-all duration-300',
          isCollapsed ? 'w-16' : 'w-64'
        )}
      >
        {/* Логотип и заголовок */}
        <div className="flex h-16 items-center border-b border-border px-4">
          {!isCollapsed ? (
            <div className="flex items-center space-x-2">
              <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                <TrendingUp className="h-4 w-4 text-primary-foreground" />
              </div>
              <span className="font-bold text-lg">Dohodometr</span>
            </div>
          ) : (
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center mx-auto cursor-default">
                  <TrendingUp className="h-4 w-4 text-primary-foreground" />
                </div>
              </TooltipTrigger>
              <TooltipContent side="right">
                <div className="font-medium">Dohodometr</div>
                <div className="text-xs text-muted-foreground">Сервис учета инвестиций</div>
              </TooltipContent>
            </Tooltip>
          )}
        </div>

        {/* Основная навигация */}
        <nav className="flex-1 overflow-y-auto py-4 px-2">
          <div className="space-y-1">
            {navigation.map((item) => (
              <NavItem
                key={item.name}
                item={item}
                isCollapsed={isCollapsed}
                isActive={pathname === item.href || pathname.startsWith(item.href + '/')}
              />
            ))}
          </div>
        </nav>

        {/* Нижняя навигация */}
        <div className="border-t border-border py-4 px-2">
          <div className="space-y-1">
            {bottomNavigation.map((item) => (
              <NavItem
                key={item.name}
                item={item}
                isCollapsed={isCollapsed}
                isActive={pathname === item.href || pathname.startsWith(item.href + '/')}
              />
            ))}
          </div>
        </div>

        {/* Кнопка сворачивания */}
        <div className="absolute -right-3 top-20 z-20">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                className="h-6 w-6 rounded-full bg-background shadow-md border-border"
                onClick={() => setIsCollapsed(!isCollapsed)}
                aria-label={isCollapsed ? 'Развернуть сайдбар' : 'Свернуть сайдбар'}
              >
                {isCollapsed ? (
                  <ChevronRight className="h-3 w-3" />
                ) : (
                  <ChevronLeft className="h-3 w-3" />
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">
              {isCollapsed ? 'Развернуть меню' : 'Свернуть меню'}
            </TooltipContent>
          </Tooltip>
        </div>
      </div>
    </TooltipProvider>
  )
}