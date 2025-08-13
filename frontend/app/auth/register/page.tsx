'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Eye, EyeOff, UserPlus, Check, X } from 'lucide-react'
import { useAuth } from '@/lib/auth/auth-context'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { validatePassword } from '@/lib/utils'

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [passwordValidation, setPasswordValidation] = useState({
    isValid: false,
    errors: [] as string[],
  })

  const { register, isAuthenticated } = useAuth()
  const router = useRouter()

  // Если пользователь уже авторизован, перенаправляем в приложение
  if (isAuthenticated) {
    router.push('/app')
    return null
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // Валидация пароля в реальном времени
    if (field === 'password') {
      const validation = validatePassword(value)
      setPasswordValidation(validation)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Валидация
    if (!passwordValidation.isValid) {
      return
    }
    
    if (formData.password !== formData.confirmPassword) {
      return
    }
    
    setIsLoading(true)

    try {
      await register(
        formData.email,
        formData.password,
        `${formData.firstName} ${formData.lastName}`.trim()
      )
      // Успешная регистрация - перенаправление произойдет автоматически
    } catch (error) {
      console.error('Registration error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const isFormValid = 
    formData.email &&
    formData.password &&
    formData.confirmPassword &&
    passwordValidation.isValid &&
    formData.password === formData.confirmPassword

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex items-center justify-center mb-4">
            <div className="p-3 bg-primary/10 rounded-full">
              <UserPlus className="h-8 w-8 text-primary" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">
            Создание аккаунта
          </CardTitle>
          <CardDescription>
            Присоединяйтесь к нашему сервису для управления инвестициями
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="firstName">Имя</Label>
                <Input
                  id="firstName"
                  type="text"
                  placeholder="Иван"
                  value={formData.firstName}
                  onChange={(e) => handleInputChange('firstName', e.target.value)}
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="lastName">Фамилия</Label>
                <Input
                  id="lastName"
                  type="text"
                  placeholder="Иванов"
                  value={formData.lastName}
                  onChange={(e) => handleInputChange('lastName', e.target.value)}
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                required
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Пароль</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Создайте надежный пароль"
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  required
                  disabled={isLoading}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
              
              {/* Индикаторы валидации пароля */}
              {formData.password && (
                <div className="space-y-1">
                  <div className="flex items-center space-x-2 text-xs">
                    {formData.password.length >= 8 ? (
                      <Check className="h-3 w-3 text-success" />
                    ) : (
                      <X className="h-3 w-3 text-destructive" />
                    )}
                    <span className={formData.password.length >= 8 ? 'text-success' : 'text-destructive'}>
                      Минимум 8 символов
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs">
                    {/[A-Z]/.test(formData.password) ? (
                      <Check className="h-3 w-3 text-success" />
                    ) : (
                      <X className="h-3 w-3 text-destructive" />
                    )}
                    <span className={/[A-Z]/.test(formData.password) ? 'text-success' : 'text-destructive'}>
                      Заглавные буквы
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs">
                    {/[a-z]/.test(formData.password) ? (
                      <Check className="h-3 w-3 text-success" />
                    ) : (
                      <X className="h-3 w-3 text-destructive" />
                    )}
                    <span className={/[a-z]/.test(formData.password) ? 'text-success' : 'text-destructive'}>
                      Строчные буквы
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs">
                    {/\d/.test(formData.password) ? (
                      <Check className="h-3 w-3 text-success" />
                    ) : (
                      <X className="h-3 w-3 text-destructive" />
                    )}
                    <span className={/\d/.test(formData.password) ? 'text-success' : 'text-destructive'}>
                      Цифры
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs">
                    {/[!@#$%^&*(),.?":{}|<>]/.test(formData.password) ? (
                      <Check className="h-3 w-3 text-success" />
                    ) : (
                      <X className="h-3 w-3 text-destructive" />
                    )}
                    <span className={/[!@#$%^&*(),.?":{}|<>]/.test(formData.password) ? 'text-success' : 'text-destructive'}>
                      Специальные символы
                    </span>
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Подтвердите пароль</Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="Повторите пароль"
                  value={formData.confirmPassword}
                  onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                  required
                  disabled={isLoading}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
              {formData.confirmPassword && formData.password !== formData.confirmPassword && (
                <p className="text-xs text-destructive">
                  Пароли не совпадают
                </p>
              )}
            </div>

            <Button 
              type="submit" 
              className="w-full" 
              disabled={!isFormValid || isLoading}
            >
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Создание аккаунта...</span>
                </div>
              ) : (
                'Создать аккаунт'
              )}
            </Button>
          </form>

          <Separator className="my-6" />

          <div className="text-center space-y-2">
            <p className="text-sm text-muted-foreground">
              Уже есть аккаунт?
            </p>
            <Button variant="outline" asChild className="w-full">
              <Link href="/auth/login">
                Войти в систему
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
