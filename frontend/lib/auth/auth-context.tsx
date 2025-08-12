'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface User {
  id: number
  email: string
  first_name?: string
  last_name?: string
  is_2fa_enabled?: boolean
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  login: (email: string, password: string, totpCode?: string, rememberMe?: boolean) => Promise<void>
  logout: () => Promise<void>
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Mock user for demo
    setUser({
      id: 1,
      email: 'demo@dohodometr.ru',
      first_name: 'Demo',
      last_name: 'User'
    })
    setIsLoading(false)
  }, [])

  const login = async (email: string, password: string, totpCode?: string, rememberMe?: boolean) => {
    // Mock login
    setUser({
      id: 1,
      email,
      first_name: 'Demo',
      last_name: 'User'
    })
  }

  const logout = async () => {
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      login,
      logout,
      isLoading
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}