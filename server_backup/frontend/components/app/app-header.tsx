'use client'

import { Bell, LogOut, Moon, Sun, User, Settings, Shield } from 'lucide-react'
import { useTheme } from 'next-themes'
import { useAuth } from '@/lib/auth/auth-context'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { MobileNavigation } from '@/components/mobile-navigation'

export function AppHeader() {
  const { user, logout } = useAuth()
  const { theme, setTheme } = useTheme()

  const getUserInitials = (firstName?: string, lastName?: string, email?: string) => {
    if (firstName && lastName) {
      return `${firstName[0]}${lastName[0]}`.toUpperCase()
    }
    if (firstName) {
      return firstName[0].toUpperCase()
    }
    if (email) {
      return email[0].toUpperCase()
    }
    return 'U'
  }

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  return (
    <header className="h-16 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-full items-center justify-between px-4 md:px-6">
        {/* Левая часть - мобильное меню */}
        <div className="flex items-center space-x-4">
          <MobileNavigation />
          {/* Здесь можно добавить хлебные крошки для десктопа */}
        </div>

        {/* Правая часть - действия пользователя */}
        <div className="flex items-center space-x-2 md:space-x-4">
          {/* Переключатель темы */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            aria-label={`Переключить на ${theme === 'dark' ? 'светлую' : 'темную'} тему`}
            className="h-9 w-9"
          >
            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            <span className="sr-only">Переключить тему</span>
          </Button>

          {/* Уведомления */}
          <Button 
            variant="ghost" 
            size="icon"
            aria-label="Уведомления"
            className="h-9 w-9 relative"
          >
            <Bell className="h-4 w-4" />
            {/* Можно добавить индикатор непрочитанных уведомлений */}
            {/* {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 h-4 w-4 bg-destructive text-destructive-foreground text-xs rounded-full flex items-center justify-center">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )} */}
            <span className="sr-only">Уведомления</span>
          </Button>

          {/* Меню пользователя */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button 
                variant="ghost" 
                className="relative h-9 w-9 rounded-full"
                aria-label="Меню пользователя"
              >
                <Avatar className="h-8 w-8">
                  <AvatarFallback>
                    {getUserInitials(user?.first_name, user?.last_name, user?.email)}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">
                    {user?.first_name && user?.last_name
                      ? `${user.first_name} ${user.last_name}`
                      : user?.email
                    }
                  </p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {user?.email}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              
              <DropdownMenuItem asChild>
                <a href="/app/profile" className="flex items-center">
                  <User className="mr-2 h-4 w-4" />
                  <span>Профиль</span>
                </a>
              </DropdownMenuItem>
              
              <DropdownMenuItem asChild>
                <a href="/app/settings" className="flex items-center">
                  <Settings className="mr-2 h-4 w-4" />
                  <span>Настройки</span>
                </a>
              </DropdownMenuItem>
              
              {user?.is_2fa_enabled && (
                <DropdownMenuItem asChild>
                  <a href="/app/settings/security" className="flex items-center">
                    <Shield className="mr-2 h-4 w-4" />
                    <span>2FA настройки</span>
                  </a>
                </DropdownMenuItem>
              )}
              
              <DropdownMenuSeparator />
              
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={handleLogout}
              >
                <LogOut className="mr-2 h-4 w-4" />
                <span>Выйти</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}
