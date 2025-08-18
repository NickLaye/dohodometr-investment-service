'use client'

import React, { createContext, useContext, useState, useEffect } from 'react'
import { api } from '@/lib/api-client'

interface User {
  id: string
  email: string
  name: string
}

interface AuthContextType {
  user: User | null
  login: (email: string, password: string, totpCode?: string) => Promise<void>
  register: (email: string, password: string, name: string) => Promise<void>
  logout: () => Promise<void>
  isLoading: boolean
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Проверка существующей сессии
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      if (typeof window === 'undefined') {
        setIsLoading(false)
        return
      }
      const access = window.localStorage.getItem('access_token')
      if (!access) {
        setUser(null)
        setIsLoading(false)
        return
      }
      const me = await api.auth.me()
      const data = me.data as any
      setUser({ id: String(data.id), email: data.email, name: data.first_name || data.email })
      setIsLoading(false)
    } catch (error) {
      setUser(null)
      setIsLoading(false)
    }
  }

  const login = async (email: string, password: string, totpCode?: string) => {
    setIsLoading(true)
    try {
      const resp = await api.auth.login(email, password, totpCode)
      const access = (resp.data as any)?.access_token as string
      const refresh = (resp.data as any)?.refresh_token as string
      if (typeof window !== 'undefined') {
        if (access) window.localStorage.setItem('access_token', access)
        if (refresh) window.localStorage.setItem('refresh_token', refresh)
      }
      // Получаем профиль
      const me = await api.auth.me()
      const data = me.data as any
      setUser({ id: String(data.id), email: data.email, name: data.first_name || data.email })
    } catch (error) {
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (email: string, password: string, name: string) => {
    setIsLoading(true)
    try {
      await api.auth.register(email, password, name, '')
      // После регистрации сразу логиним
      await login(email, password)
    } catch (error) {
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      await api.auth.logout()
    } catch {}
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('access_token')
      window.localStorage.removeItem('refresh_token')
    }
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout, isLoading, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    // Во время SSR возвращаем значения по умолчанию вместо ошибки
    if (typeof window === 'undefined') {
      return {
        user: null,
        login: async (_email: string, _password: string) => {},
        register: async (_email: string, _password: string, _name: string) => {},
        logout: () => {},
        isLoading: false,
        isAuthenticated: false,
      } as AuthContextType
    }
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}