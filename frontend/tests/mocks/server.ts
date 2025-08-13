/**
 * Mock Service Worker (MSW) server setup for testing.
 * 
 * This file sets up MSW to intercept HTTP requests during testing
 * and return mock responses, allowing us to test components without
 * making real API calls.
 */

import { setupServer } from 'msw/node';
import { rest } from 'msw';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Mock data
const mockUser = {
  id: 1,
  email: 'test@example.com',
  username: 'testuser',
  full_name: 'Test User',
  is_active: true,
  is_superuser: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockPortfolios = [
  {
    id: 1,
    name: 'Growth Portfolio',
    description: 'Long-term growth focused portfolio',
    base_currency: 'USD',
    total_value: 50000.0,
    is_active: true,
    user_id: 1,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'Conservative Portfolio',
    description: 'Low-risk conservative portfolio',
    base_currency: 'USD',
    total_value: 25000.0,
    is_active: true,
    user_id: 1,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
];

const mockTransactions = [
  {
    id: 1,
    date: '2024-01-15',
    type: 'buy',
    symbol: 'AAPL',
    quantity: 10,
    price: 150.0,
    currency: 'USD',
    commission: 1.0,
    description: 'Buy Apple shares',
    portfolio_id: 1,
    account_id: 1,
    created_at: '2024-01-15T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z',
  },
  {
    id: 2,
    date: '2024-01-16',
    type: 'sell',
    symbol: 'GOOGL',
    quantity: 2,
    price: 2800.0,
    currency: 'USD',
    commission: 2.0,
    description: 'Sell Google shares',
    portfolio_id: 1,
    account_id: 1,
    created_at: '2024-01-16T00:00:00Z',
    updated_at: '2024-01-16T00:00:00Z',
  },
];

// API handlers
export const handlers = [
  // Authentication endpoints
  rest.post(`${API_BASE_URL}/api/v1/auth/login`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        access_token: 'mock-jwt-token',
        refresh_token: 'mock-refresh-token',
        token_type: 'bearer',
        user: mockUser,
      })
    );
  }),

  rest.post(`${API_BASE_URL}/api/v1/auth/register`, (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        ...mockUser,
        id: Math.floor(Math.random() * 1000),
      })
    );
  }),

  rest.get(`${API_BASE_URL}/api/v1/auth/me`, (req, res, ctx) => {
    const authHeader = req.headers.get('authorization');
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res(
        ctx.status(401),
        ctx.json({ detail: 'Authentication required' })
      );
    }

    return res(ctx.status(200), ctx.json(mockUser));
  }),

  rest.post(`${API_BASE_URL}/api/v1/auth/logout`, (req, res, ctx) => {
    return res(ctx.status(200), ctx.json({ message: 'Logged out successfully' }));
  }),

  // Portfolio endpoints
  rest.get(`${API_BASE_URL}/api/v1/portfolios`, (req, res, ctx) => {
    const authHeader = req.headers.get('authorization');
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res(
        ctx.status(401),
        ctx.json({ detail: 'Authentication required' })
      );
    }

    const skip = Number(req.url.searchParams.get('skip')) || 0;
    const limit = Number(req.url.searchParams.get('limit')) || 100;

    const paginatedPortfolios = mockPortfolios.slice(skip, skip + limit);

    return res(ctx.status(200), ctx.json(paginatedPortfolios));
  }),

  rest.get(`${API_BASE_URL}/api/v1/portfolios/:id`, (req, res, ctx) => {
    const { id } = req.params;
    const portfolioId = Number(id);
    
    const portfolio = mockPortfolios.find(p => p.id === portfolioId);
    
    if (!portfolio) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Portfolio not found' })
      );
    }

    return res(ctx.status(200), ctx.json(portfolio));
  }),

  rest.post(`${API_BASE_URL}/api/v1/portfolios`, (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        id: Math.floor(Math.random() * 1000),
        ...req.body,
        user_id: mockUser.id,
        total_value: 0,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
    );
  }),

  rest.put(`${API_BASE_URL}/api/v1/portfolios/:id`, (req, res, ctx) => {
    const { id } = req.params;
    const portfolioId = Number(id);
    
    const portfolio = mockPortfolios.find(p => p.id === portfolioId);
    
    if (!portfolio) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Portfolio not found' })
      );
    }

    return res(
      ctx.status(200),
      ctx.json({
        ...portfolio,
        ...req.body,
        updated_at: new Date().toISOString(),
      })
    );
  }),

  rest.delete(`${API_BASE_URL}/api/v1/portfolios/:id`, (req, res, ctx) => {
    const { id } = req.params;
    const portfolioId = Number(id);
    
    const portfolio = mockPortfolios.find(p => p.id === portfolioId);
    
    if (!portfolio) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Portfolio not found' })
      );
    }

    return res(ctx.status(204));
  }),

  // Transaction endpoints
  rest.get(`${API_BASE_URL}/api/v1/transactions`, (req, res, ctx) => {
    const portfolioId = req.url.searchParams.get('portfolio_id');
    const skip = Number(req.url.searchParams.get('skip')) || 0;
    const limit = Number(req.url.searchParams.get('limit')) || 100;

    let filteredTransactions = mockTransactions;
    
    if (portfolioId) {
      filteredTransactions = mockTransactions.filter(
        t => t.portfolio_id === Number(portfolioId)
      );
    }

    const paginatedTransactions = filteredTransactions.slice(skip, skip + limit);

    return res(ctx.status(200), ctx.json(paginatedTransactions));
  }),

  rest.post(`${API_BASE_URL}/api/v1/transactions`, (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        id: Math.floor(Math.random() * 1000),
        ...req.body,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
    );
  }),

  rest.post(`${API_BASE_URL}/api/v1/transactions/import`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        imported_count: 5,
        skipped_count: 1,
        error_count: 0,
        errors: [],
      })
    );
  }),

  // Analytics endpoints
  rest.get(`${API_BASE_URL}/api/v1/analytics/performance`, (req, res, ctx) => {
    const portfolioId = req.url.searchParams.get('portfolio_id');
    
    if (!portfolioId) {
      return res(
        ctx.status(400),
        ctx.json({ detail: 'Portfolio ID is required' })
      );
    }

    return res(
      ctx.status(200),
      ctx.json({
        total_return: 15.5,
        annualized_return: 12.3,
        volatility: 8.7,
        sharpe_ratio: 1.42,
        max_drawdown: -5.2,
        start_value: 10000.0,
        end_value: 11550.0,
        period_days: 365,
      })
    );
  }),

  rest.get(`${API_BASE_URL}/api/v1/analytics/allocation`, (req, res, ctx) => {
    const portfolioId = req.url.searchParams.get('portfolio_id');
    
    if (!portfolioId) {
      return res(
        ctx.status(400),
        ctx.json({ detail: 'Portfolio ID is required' })
      );
    }

    return res(
      ctx.status(200),
      ctx.json({
        by_sector: {
          Technology: 45.5,
          Healthcare: 22.3,
          Finance: 18.7,
          Energy: 8.2,
          Other: 5.3,
        },
        by_currency: {
          USD: 85.5,
          EUR: 10.2,
          RUB: 4.3,
        },
        by_asset_type: {
          stocks: 70.5,
          bonds: 20.3,
          etf: 9.2,
        },
      })
    );
  }),

  // Health check
  rest.get(`${API_BASE_URL}/health`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        services: {
          postgres: 'healthy',
          redis: 'healthy',
          minio: 'healthy',
        },
      })
    );
  }),

  // Fallback handler for unmatched requests
  rest.all('*', (req, res, ctx) => {
    console.warn(`Unhandled ${req.method} request to ${req.url.toString()}`);
    
    return res(
      ctx.status(404),
      ctx.json({ detail: 'Not found' })
    );
  }),
];

// Create and export the server
export const server = setupServer(...handlers);
