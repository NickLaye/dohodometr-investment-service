/**
 * Централизованный API клиент для подключения к backend
 */

import axios, { AxiosResponse, AxiosError } from 'axios'

// Конфигурация базового URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Создание axios инстанса
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
})

// Интерцептор для добавления токена авторизации
apiClient.interceptors.request.use(
  (config) => {
    // Получаем токен из localStorage или cookies
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Интерцептор для обработки ответов
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error: AxiosError) => {
    // Обработка ошибки авторизации
    if (error.response?.status === 401) {
      // Очищаем токен и перенаправляем на логин
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      
      // Перенаправление на логин (только в браузере)
      if (typeof window !== 'undefined') {
        window.location.href = '/auth/login'
      }
    }
    
    // Логируем ошибки в консоль для разработки
    if (process.env.NODE_ENV === 'development') {
      console.error('API Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        data: error.response?.data,
      })
    }
    
    return Promise.reject(error)
  }
)

// Типы для API
export interface Portfolio {
  id: number
  name: string
  description?: string
  totalValue: number
  dailyChange: number
  dailyChangePercent: number
  assetsCount: number
  base_currency: string
  created_at: string
  updated_at: string
}

export interface TaxCalculationRequest {
  portfolio_ids: number[]
  tax_year?: number
  is_resident: boolean
}

export interface TaxCalculationResult {
  total_income: number
  total_expenses: number
  taxable_income: number
  ndfl_base: number
  ndfl_amount: number
  ndfl_rate: number
  ldv_exemption: number
  iis_deduction: number
  loss_carryover: number
  stock_pnl: number
  bond_pnl: number
  dividend_income: number
  coupon_income: number
  tax_year: number
  calculation_date: string
  recommendations: string[]
}

export interface IISStrategyRequest {
  annual_income: number
  expected_return: number
  investment_horizon: number
  annual_contribution: number
}

export interface IISStrategyResult {
  type_a_net_result: number
  type_b_net_result: number
  type_a_deductions: number
  type_a_ndfl: number
  type_b_ndfl: number
  optimal_strategy: string
  advantage_amount: number
}

// API методы
export const api = {
  // Аутентификация
  auth: {
    login: (email: string, password: string, totp_code?: string) =>
      apiClient.post('/api/v1/auth/login', { email, password, totp_code }),
    
    register: (email: string, password: string, first_name: string, last_name: string) =>
      apiClient.post('/api/v1/auth/register', { email, password, first_name, last_name }),
    
    refresh: (refresh_token: string) =>
      apiClient.post('/api/v1/auth/refresh', { refresh_token }),
    
    logout: () =>
      apiClient.post('/api/v1/auth/logout'),
    
    me: () =>
      apiClient.get('/api/v1/auth/me'),
  },

  // Портфели
  portfolios: {
    getAll: (): Promise<AxiosResponse<Portfolio[]>> =>
      apiClient.get('/api/v1/portfolios/'),
    
    getById: (id: number): Promise<AxiosResponse<Portfolio>> =>
      apiClient.get(`/api/v1/portfolios/${id}`),
    
    create: (data: Partial<Portfolio>) =>
      apiClient.post('/api/v1/portfolios/', data),
    
    update: (id: number, data: Partial<Portfolio>) =>
      apiClient.put(`/api/v1/portfolios/${id}`, data),
    
    delete: (id: number) =>
      apiClient.delete(`/api/v1/portfolios/${id}`),
    
    getSummary: (id: number) =>
      apiClient.get(`/api/v1/portfolios/${id}/summary`),
  },

  // Налоговый калькулятор
  tax: {
    calculate: (data: TaxCalculationRequest): Promise<AxiosResponse<TaxCalculationResult>> =>
      apiClient.post('/api/v1/tax/calculate', data),
    
    iisStrategy: (data: IISStrategyRequest): Promise<AxiosResponse<IISStrategyResult>> =>
      apiClient.post('/api/v1/tax/iis-strategy', data),
    
    demoCalculation: (): Promise<AxiosResponse<{ tax_calculation: TaxCalculationResult }>> =>
      apiClient.get('/api/v1/tax/demo-calculation'),
    
    taxDeadlines: () =>
      apiClient.get('/api/v1/tax/tax-deadlines'),
    
    taxRates: () =>
      apiClient.get('/api/v1/tax/tax-rates'),
    
    health: () =>
      apiClient.get('/api/v1/tax/health'),
  },

  // Транзакции
  transactions: {
    getAll: (params?: any) =>
      apiClient.get('/api/v1/transactions/', { params }),
    
    create: (data: any) =>
      apiClient.post('/api/v1/transactions/', data),
    
    delete: (id: number) =>
      apiClient.delete(`/api/v1/transactions/${id}`),
  },

  // Аналитика
  analytics: {
    getPerformance: (portfolioId: number, params?: any) =>
      apiClient.get(`/api/v1/analytics/performance`, { params: { portfolio_id: portfolioId, ...params } }),
    
    getAllocation: (portfolioId: number) =>
      apiClient.get(`/api/v1/analytics/allocation`, { params: { portfolio_id: portfolioId } }),
    
    getPnLBreakdown: (portfolioId: number, params?: any) =>
      apiClient.get(`/api/v1/analytics/pnl-breakdown`, { params: { portfolio_id: portfolioId, ...params } }),
  },

  // Общие методы
  health: () =>
    apiClient.get('/health'),
  
  info: () =>
    apiClient.get('/api/v1/'),
}

export default apiClient
