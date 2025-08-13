// Mock API для демо-версии

interface Portfolio {
  id: number
  name: string
  description?: string
  totalValue: number
  dailyChange: number
  dailyChangePercent: number
  assetsCount: number
}

interface PerformanceData {
  date: string
  value: number
  return: number
}

// Mock данные
const mockPortfolios: Portfolio[] = [
  {
    id: 1,
    name: 'Основной портфель',
    description: 'Долгосрочные инвестиции',
    totalValue: 2450000,
    dailyChange: 15240,
    dailyChangePercent: 0.8,
    assetsCount: 24
  },
  {
    id: 2,
    name: 'Спекулятивный',
    description: 'Краткосрочная торговля',
    totalValue: 850000,
    dailyChange: -8500,
    dailyChangePercent: -1.2,
    assetsCount: 15
  }
]

const mockPerformance: PerformanceData[] = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  value: 2450000 + Math.random() * 100000 - 50000,
  return: (Math.random() - 0.5) * 0.1
}))

export const portfoliosApi = {
  getPortfolios: async (): Promise<Portfolio[]> => {
    await new Promise(resolve => setTimeout(resolve, 500))
    return mockPortfolios
  },

  getPortfolio: async (id: number): Promise<Portfolio | null> => {
    await new Promise(resolve => setTimeout(resolve, 300))
    return mockPortfolios.find(p => p.id === id) || null
  }
}

export const analyticsApi = {
  getPerformance: async (portfolioId: number, period: string): Promise<PerformanceData[]> => {
    await new Promise(resolve => setTimeout(resolve, 800))
    return mockPerformance
  }
}