'use client'

import { useAuth } from '@/lib/auth/auth-context'
import { useRouter } from 'next/navigation'
import { AppSidebar } from '@/components/app/app-sidebar'
import { AppHeader } from '@/components/app/app-header'
import { LoadingSpinner } from '@/components/ui/loading-spinner'

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()

  // Показываем загрузку пока проверяем авторизацию
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  // Если не авторизован, перенаправляем на страницу входа
  if (!isAuthenticated) {
    router.push('/auth/login')
    return null
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="flex h-screen">
        {/* Боковая панель */}
        <AppSidebar />
        
        {/* Основной контент */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Заголовок */}
          <AppHeader />
          
          {/* Контент страницы */}
          <main className="flex-1 overflow-y-auto p-6">
            <div className="max-w-7xl mx-auto">
              {children}
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}
