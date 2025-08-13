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
  Menu,
  PieChart,
  Settings,
  Target,
  TrendingUp,
  Upload,
  Wallet,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import { Separator } from '@/components/ui/separator'

const navigation = [
  {
    name: 'Обзор',
    href: '/app',
    icon: Home,
    description: 'Общий обзор портфелей и показателей'
  },
  {
    name: 'Портфели',
    href: '/app/portfolios',
    icon: Briefcase,
    description: 'Управление инвестиционными портфелями'
  },
  {
    name: 'Транзакции',
    href: '/app/transactions',
    icon: Wallet,
    description: 'История операций и сделок'
  },
  {
    name: 'Аналитика',
    href: '/app/analytics',
    icon: BarChart3,
    description: 'Подробный анализ доходности',
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
    description: 'Расчет налогов и оптимизация'
  },
  {
    name: 'Импорт',
    href: '/app/import',
    icon: Upload,
    description: 'Импорт данных от брокеров'
  },
  {
    name: 'Планирование',
    href: '/app/planning',
    icon: Calendar,
    description: 'Цели и планирование инвестиций'
  },
  {
    name: 'Настройки',
    href: '/app/settings',
    icon: Settings,
    description: 'Персональные настройки'
  },
]

interface MobileNavItemProps {
  item: typeof navigation[0]
  onItemClick?: () => void
}

function MobileNavItem({ item, onItemClick }: MobileNavItemProps) {
  const pathname = usePathname()
  const isActive = pathname === item.href || pathname.startsWith(item.href + '/')

  return (
    <div className="space-y-1">
      <Link
        href={item.href}
        onClick={onItemClick}
        className={cn(
          'flex items-center space-x-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
          isActive
            ? 'bg-primary text-primary-foreground'
            : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
        )}
      >
        <item.icon className="h-5 w-5 shrink-0" />
        <div className="flex-1 text-left">
          <div className="font-medium">{item.name}</div>
          {item.description && (
            <div className="text-xs opacity-75 mt-0.5">{item.description}</div>
          )}
        </div>
      </Link>
      
      {/* Sub-navigation for children */}
      {item.children && (
        <div className="pl-8 space-y-1">
          {item.children.map((child) => {
            const isChildActive = pathname === child.href
            return (
              <Link
                key={child.href}
                href={child.href}
                onClick={onItemClick}
                className={cn(
                  'flex items-center space-x-2 rounded-md px-2 py-1.5 text-sm transition-colors',
                  isChildActive
                    ? 'bg-primary/10 text-primary font-medium'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
              >
                <child.icon className="h-4 w-4" />
                <span>{child.name}</span>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}

interface MobileNavigationProps {
  className?: string
}

export function MobileNavigation({ className }: MobileNavigationProps) {
  const [open, setOpen] = useState(false)

  const handleItemClick = () => {
    setOpen(false)
  }

  return (
    <div className={cn('md:hidden', className)}>
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="h-10 w-10"
            aria-label="Открыть меню навигации"
          >
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-80 p-0">
          <SheetHeader className="p-6 pb-3">
            <SheetTitle className="text-left">
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                  <TrendingUp className="h-4 w-4 text-primary-foreground" />
                </div>
                <span className="font-bold">Dohodometr</span>
              </div>
            </SheetTitle>
            <SheetDescription className="text-left">
              Сервис учета инвестиций
            </SheetDescription>
          </SheetHeader>
          
          <Separator />
          
          <nav className="flex-1 overflow-y-auto p-4">
            <div className="space-y-2">
              {navigation.map((item) => (
                <MobileNavItem
                  key={item.href}
                  item={item}
                  onItemClick={handleItemClick}
                />
              ))}
            </div>
          </nav>
          
          <Separator />
          
          <div className="p-4">
            <div className="text-xs text-muted-foreground text-center">
              © 2025 Dohodometr.ru
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  )
}

export default MobileNavigation
