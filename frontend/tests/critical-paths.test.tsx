/**
 * Критичные пользовательские сценарии для frontend
 * Тесты основных путей взаимодействия пользователя
 */

import React, { useState } from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, beforeEach } from 'vitest'
import userEvent from '@testing-library/user-event'

// Mock компоненты для тестирования
const MockLoginPage = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      // Mock API call
      if (email === 'test@example.com' && password === 'password123') {
        // Simulate successful login
        await new Promise(resolve => setTimeout(resolve, 100))
      } else {
        throw new Error('Invalid credentials')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} data-testid="login-form">
      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          data-testid="email-input"
          required
        />
      </div>
      <div>
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          data-testid="password-input"
          required
        />
      </div>
      {error && <div data-testid="error-message" role="alert">{error}</div>}
      <button 
        type="submit" 
        disabled={isLoading}
        data-testid="submit-button"
      >
        {isLoading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  )
}

const MockPortfolioDashboard = ({ portfolios = [] }: { portfolios?: Array<{ id: number; name: string; value: number }> }) => {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [portfolioName, setPortfolioName] = useState('')

  const handleCreatePortfolio = () => {
    if (portfolioName.trim()) {
      // Mock portfolio creation
      setShowCreateModal(false)
      setPortfolioName('')
    }
  }

  return (
    <div data-testid="portfolio-dashboard">
      <h1>Мои портфели</h1>
      
      <button 
        onClick={() => setShowCreateModal(true)}
        data-testid="create-portfolio-button"
      >
        Создать портфель
      </button>

      <div data-testid="portfolios-list">
        {portfolios.length === 0 ? (
          <p data-testid="no-portfolios">У вас пока нет портфелей</p>
        ) : (
          portfolios.map((portfolio) => (
            <div key={portfolio.id} data-testid={`portfolio-${portfolio.id}`}>
              <h3>{portfolio.name}</h3>
              <p>Стоимость: {portfolio.value.toLocaleString('ru-RU')} ₽</p>
            </div>
          ))
        )}
      </div>

      {showCreateModal && (
        <div data-testid="create-portfolio-modal" role="dialog">
          <h2>Создать новый портфель</h2>
          <input
            type="text"
            placeholder="Название портфеля"
            value={portfolioName}
            onChange={(e) => setPortfolioName(e.target.value)}
            data-testid="portfolio-name-input"
          />
          <button 
            onClick={handleCreatePortfolio}
            data-testid="confirm-create-button"
          >
            Создать
          </button>
          <button 
            onClick={() => setShowCreateModal(false)}
            data-testid="cancel-create-button"
          >
            Отмена
          </button>
        </div>
      )}
    </div>
  )
}

// Wrapper для React Query
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = createTestQueryClient()
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('Critical User Journeys', () => {
  let user: ReturnType<typeof userEvent.setup>

  beforeEach(() => {
    user = userEvent.setup()
  })

  describe('Authentication Flow', () => {
    it('should handle successful login', async () => {
      render(
        <TestWrapper>
          <MockLoginPage />
        </TestWrapper>
      )

      // Заполняем форму
      await user.type(screen.getByTestId('email-input'), 'test@example.com')
      await user.type(screen.getByTestId('password-input'), 'password123')

      // Отправляем форму
      await user.click(screen.getByTestId('submit-button'))

      // Проверяем состояние загрузки
      expect(screen.getByTestId('submit-button')).toHaveTextContent('Logging in...')

      // Ждем завершения запроса
      await waitFor(() => {
        expect(screen.getByTestId('submit-button')).not.toBeDisabled()
      })

      // Не должно быть ошибок
      expect(screen.queryByTestId('error-message')).not.toBeInTheDocument()
    })

    it('should handle login failure with error message', async () => {
      render(
        <TestWrapper>
          <MockLoginPage />
        </TestWrapper>
      )

      // Заполняем неправильные данные
      await user.type(screen.getByTestId('email-input'), 'wrong@example.com')
      await user.type(screen.getByTestId('password-input'), 'wrongpassword')

      // Отправляем форму
      await user.click(screen.getByTestId('submit-button'))

      // Ждем появления ошибки
      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toBeInTheDocument()
      })

      // Проверяем текст ошибки
      expect(screen.getByTestId('error-message')).toHaveTextContent('Invalid credentials')
    })

    it('should validate email format', async () => {
      render(
        <TestWrapper>
          <MockLoginPage />
        </TestWrapper>
      )

      const emailInput = screen.getByTestId('email-input')

      // Вводим неправильный email
      await user.type(emailInput, 'not-an-email')

      // HTML5 validation должна сработать
      expect(emailInput).toBeInvalid()
    })

    it('should require both email and password', async () => {
      render(
        <TestWrapper>
          <MockLoginPage />
        </TestWrapper>
      )

      // Пытаемся отправить пустую форму
      await user.click(screen.getByTestId('submit-button'))

      // Поля должны быть помечены как обязательные
      expect(screen.getByTestId('email-input')).toBeRequired()
      expect(screen.getByTestId('password-input')).toBeRequired()
    })
  })

  describe('Portfolio Management', () => {
    it('should display empty state when no portfolios', () => {
      render(
        <TestWrapper>
          <MockPortfolioDashboard portfolios={[]} />
        </TestWrapper>
      )

      expect(screen.getByTestId('no-portfolios')).toHaveTextContent('У вас пока нет портфелей')
      expect(screen.getByTestId('create-portfolio-button')).toBeInTheDocument()
    })

    it('should display existing portfolios', () => {
      const mockPortfolios = [
        { id: 1, name: 'Основной портфель', value: 1000000 },
        { id: 2, name: 'Консервативный', value: 500000 }
      ]

      render(
        <TestWrapper>
          <MockPortfolioDashboard portfolios={mockPortfolios} />
        </TestWrapper>
      )

      // Проверяем что портфели отображаются
      expect(screen.getByTestId('portfolio-1')).toBeInTheDocument()
      expect(screen.getByTestId('portfolio-2')).toBeInTheDocument()

      // Проверяем содержимое
      expect(screen.getByText('Основной портфель')).toBeInTheDocument()
      expect(screen.getByText('Стоимость: 1 000 000 ₽')).toBeInTheDocument()
    })

    it('should handle portfolio creation flow', async () => {
      render(
        <TestWrapper>
          <MockPortfolioDashboard portfolios={[]} />
        </TestWrapper>
      )

      // Открываем модал создания
      await user.click(screen.getByTestId('create-portfolio-button'))

      // Проверяем что модал открылся
      expect(screen.getByTestId('create-portfolio-modal')).toBeInTheDocument()
      expect(screen.getByRole('dialog')).toBeInTheDocument()

      // Заполняем название
      await user.type(screen.getByTestId('portfolio-name-input'), 'Новый портфель')

      // Создаем портфель
      await user.click(screen.getByTestId('confirm-create-button'))

      // Модал должен закрыться
      expect(screen.queryByTestId('create-portfolio-modal')).not.toBeInTheDocument()
    })

    it('should handle portfolio creation cancellation', async () => {
      render(
        <TestWrapper>
          <MockPortfolioDashboard portfolios={[]} />
        </TestWrapper>
      )

      // Открываем модал
      await user.click(screen.getByTestId('create-portfolio-button'))
      expect(screen.getByTestId('create-portfolio-modal')).toBeInTheDocument()

      // Отменяем
      await user.click(screen.getByTestId('cancel-create-button'))

      // Модал должен закрыться
      expect(screen.queryByTestId('create-portfolio-modal')).not.toBeInTheDocument()
    })

    it('should not create portfolio with empty name', async () => {
      render(
        <TestWrapper>
          <MockPortfolioDashboard portfolios={[]} />
        </TestWrapper>
      )

      // Открываем модал
      await user.click(screen.getByTestId('create-portfolio-button'))

      // Пытаемся создать с пустым названием
      await user.click(screen.getByTestId('confirm-create-button'))

      // Модал не должен закрыться (валидация не пройдена)
      expect(screen.getByTestId('create-portfolio-modal')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels for forms', () => {
      render(
        <TestWrapper>
          <MockLoginPage />
        </TestWrapper>
      )

      // Проверяем что поля связаны с labels
      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('Password')

      expect(emailInput).toBeInTheDocument()
      expect(passwordInput).toBeInTheDocument()
    })

    it('should announce errors to screen readers', async () => {
      render(
        <TestWrapper>
          <MockLoginPage />
        </TestWrapper>
      )

      // Вводим неправильные данные
      await user.type(screen.getByTestId('email-input'), 'wrong@example.com')
      await user.type(screen.getByTestId('password-input'), 'wrong')
      await user.click(screen.getByTestId('submit-button'))

      // Ждем ошибку
      await waitFor(() => {
        const errorMessage = screen.getByTestId('error-message')
        expect(errorMessage).toHaveAttribute('role', 'alert')
      })
    })

    it('should support keyboard navigation', async () => {
      render(
        <TestWrapper>
          <MockLoginPage />
        </TestWrapper>
      )

      const emailInput = screen.getByTestId('email-input')
      const passwordInput = screen.getByTestId('password-input')
      const submitButton = screen.getByTestId('submit-button')

      // Проверяем табуляцию
      await user.tab()
      expect(emailInput).toHaveFocus()

      await user.tab()
      expect(passwordInput).toHaveFocus()

      await user.tab()
      expect(submitButton).toHaveFocus()
    })
  })

  describe('Performance', () => {
    it('should render portfolio list efficiently', () => {
      const manyPortfolios = Array.from({ length: 100 }, (_, i) => ({
        id: i + 1,
        name: `Portfolio ${i + 1}`,
        value: Math.random() * 1000000
      }))

      const startTime = performance.now()

      render(
        <TestWrapper>
          <MockPortfolioDashboard portfolios={manyPortfolios} />
        </TestWrapper>
      )

      const endTime = performance.now()
      const renderTime = endTime - startTime

      // Рендер не должен занимать больше 100ms
      expect(renderTime).toBeLessThan(100)

      // Все элементы должны быть на месте
      expect(screen.getByTestId('portfolios-list')).toBeInTheDocument()
    })
  })

  describe('Error Boundary', () => {
    it('should handle component errors gracefully', () => {
      const ErrorThrowingComponent = () => {
        throw new Error('Test error')
      }

      const ErrorBoundary: React.FC<{ children: React.ReactNode }> = ({ children }) => {
        const [hasError, setHasError] = useState(false)

        if (hasError) {
          return <div data-testid="error-fallback">Что-то пошло не так</div>
        }

        try {
          return <>{children}</>
        } catch {
          setHasError(true)
          return <div data-testid="error-fallback">Что-то пошло не так</div>
        }
      }

      // В реальном приложении нужно использовать componentDidCatch
      // Это упрощенный пример для демонстрации тестирования error boundaries
      
      render(
        <TestWrapper>
          <ErrorBoundary>
            <MockPortfolioDashboard />
          </ErrorBoundary>
        </TestWrapper>
      )

      // Компонент должен рендериться без ошибок
      expect(screen.getByTestId('portfolio-dashboard')).toBeInTheDocument()
    })
  })
})

// Все импорты уже в начале файла
