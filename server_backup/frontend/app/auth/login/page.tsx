'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Eye, EyeOff, LogIn, Shield } from 'lucide-react'
import { useAuth } from '@/lib/auth/auth-context'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Checkbox } from '@/components/ui/checkbox'
import { useToast } from '@/hooks/use-toast'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [totpCode, setTotpCode] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [requires2FA, setRequires2FA] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [errors, setErrors] = useState<{ email?: string; password?: string; totp?: string }>({})

  const { login, isAuthenticated } = useAuth()
  const { toast } = useToast()
  const router = useRouter()

  // Если пользователь уже авторизован, перенаправляем в приложение
  if (isAuthenticated) {
    router.push('/app')
    return null
  }

  const validateForm = () => {
    const newErrors: typeof errors = {}
    
    if (!email) {
      newErrors.email = 'Email обязателен'
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Некорректный email'
    }
    
    if (!password) {
      newErrors.password = 'Пароль обязателен'
    } else if (password.length < 6) {
      newErrors.password = 'Пароль должен содержать минимум 6 символов'
    }
    
    if (requires2FA && !totpCode) {
      newErrors.totp = 'Код 2FA обязателен'
    } else if (requires2FA && totpCode.length !== 6) {
      newErrors.totp = 'Код должен содержать 6 цифр'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }
    
    setIsLoading(true)
    setErrors({})

    try {
      await login(email, password, totpCode || undefined, rememberMe)
      // Успешный вход - перенаправление произойдет автоматически
    } catch (error: any) {
      // Проверяем, требуется ли 2FA
      if (error.response?.status === 422 && error.response?.data?.detail?.includes('2FA')) {
        setRequires2FA(true)
        toast({
          title: 'Требуется двухфакторная аутентификация',
          description: 'Введите код из приложения аутентификатора',
        })
      } else {
        const errorMessage = error.response?.data?.detail || 'Ошибка входа'
        toast({
          title: 'Ошибка входа',
          description: errorMessage,
          variant: 'destructive',
        })
        
        if (error.response?.status === 401) {
          setErrors({ email: 'Неверный email или пароль' })
        }
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-4">
      {/* Skip link for screen readers */}
      <a 
        href="#main-content" 
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-primary text-primary-foreground px-4 py-2 rounded z-50"
      >
        Перейти к форме входа
      </a>
      
      <Card className="w-full max-w-md sm:max-w-lg" id="main-content">
        <CardHeader className="space-y-1 text-center">
          <div className="flex items-center justify-center mb-4">
            <div className="p-3 bg-primary/10 rounded-full">
              <LogIn className="h-8 w-8 text-primary" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">
            Добро пожаловать
          </CardTitle>
          <CardDescription>
            Войдите в свой аккаунт для доступа к портфелям
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
                aria-invalid={!!errors.email}
                aria-describedby={errors.email ? "email-error" : "email-help"}
                autoComplete="email"
              />
              {errors.email && (
                <div id="email-error" role="alert" className="text-destructive text-sm">
                  {errors.email}
                </div>
              )}
              <div id="email-help" className="sr-only">
                Введите ваш email адрес для входа в систему
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Пароль</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Введите пароль"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoading}
                  className="pr-10"
                  aria-invalid={!!errors.password}
                  aria-describedby={errors.password ? "password-error" : "password-help"}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
              {errors.password && (
                <div id="password-error" role="alert" className="text-destructive text-sm">
                  {errors.password}
                </div>
              )}
              <div id="password-help" className="sr-only">
                Введите ваш пароль для входа в систему
              </div>
            </div>

            {requires2FA && (
              <div className="space-y-2">
                <Label htmlFor="totp">Код двухфакторной аутентификации</Label>
                <div className="relative">
                  <Input
                    id="totp"
                    type="text"
                    placeholder="000000"
                    value={totpCode}
                    onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    maxLength={6}
                    required={requires2FA}
                    disabled={isLoading}
                    className="pl-10 text-center tracking-widest"
                    aria-invalid={!!errors.totp}
                    aria-describedby={errors.totp ? "totp-error" : "totp-help"}
                    autoComplete="one-time-code"
                  />
                  <Shield className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                </div>
                {errors.totp && (
                  <div id="totp-error" role="alert" className="text-destructive text-sm">
                    {errors.totp}
                  </div>
                )}
                <div id="totp-help" className="text-xs text-muted-foreground">
                  Введите 6-значный код из приложения Google Authenticator или Authy
                </div>
              </div>
            )}

            {/* Remember Me */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="remember" 
                  checked={rememberMe}
                  onCheckedChange={(checked) => setRememberMe(checked as boolean)}
                />
                <Label 
                  htmlFor="remember" 
                  className="text-sm font-normal cursor-pointer"
                >
                  Запомнить меня
                </Label>
              </div>
              <Link 
                href="/auth/forgot-password"
                className="text-sm text-muted-foreground hover:text-primary transition-colors"
              >
                Забыли пароль?
              </Link>
            </div>

            <Button 
              type="submit" 
              className="w-full" 
              disabled={isLoading}
              aria-describedby="submit-help"
            >
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Вход...</span>
                </div>
              ) : (
                'Войти'
              )}
            </Button>
            <div id="submit-help" className="sr-only">
              Нажмите для входа в систему с указанными данными
            </div>
          </form>

          <Separator className="my-6" />

          <div className="text-center space-y-2">
            <p className="text-sm text-muted-foreground">
              Нет аккаунта?
            </p>
            <Button variant="outline" asChild className="w-full">
              <Link href="/auth/register">
                Создать аккаунт
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
