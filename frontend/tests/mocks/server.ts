/**
 * MSW Server Setup for Testing
 * 
 * This file sets up MSW to intercept HTTP requests during testing
 * and return mock responses, allowing us to test components without
 * making real API calls.
 */

import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Mock data
const mockUser = {
  id: 1,
  email: 'test@example.com',
  name: 'Test User',
  created_at: '2024-01-01T00:00:00Z'
};

const mockPortfolios = [
  {
    id: 1,
    name: 'Основной портфель',
    description: 'Мой основной инвестиционный портфель',
    total_value: 1500000,
    daily_change: 15000,
    daily_change_percent: 1.0,
    user_id: 1,
    created_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 2,
    name: 'Консервативный портфель',
    description: 'Низкорисковые инвестиции',
    total_value: 800000,
    daily_change: -5000,
    daily_change_percent: -0.6,
    user_id: 1,
    created_at: '2024-01-02T00:00:00Z'
  }
];

export const handlers = [
  // Authentication endpoints
  http.post(`${API_BASE_URL}/api/v1/auth/login`, () => {
    return HttpResponse.json({
      access_token: 'mock-access-token',
      token_type: 'bearer',
      expires_in: 3600,
      user: mockUser
    });
  }),

  http.post(`${API_BASE_URL}/api/v1/auth/register`, () => {
    return HttpResponse.json({
      message: 'User registered successfully',
      user: mockUser
    });
  }),

  http.post(`${API_BASE_URL}/api/v1/auth/logout`, () => {
    return HttpResponse.json({
      message: 'Successfully logged out'
    });
  }),

  // User endpoints
  http.get(`${API_BASE_URL}/api/v1/users/me`, () => {
    return HttpResponse.json(mockUser);
  }),

  // Portfolio endpoints
  http.get(`${API_BASE_URL}/api/v1/portfolios`, () => {
    return HttpResponse.json(mockPortfolios);
  }),

  http.get(`${API_BASE_URL}/api/v1/portfolios/:id`, ({ params }) => {
    const { id } = params;
    const portfolio = mockPortfolios.find(p => p.id === parseInt(id as string));
    
    if (!portfolio) {
      return HttpResponse.json({ error: 'Portfolio not found' }, { status: 404 });
    }
    
    return HttpResponse.json(portfolio);
  }),

  http.post(`${API_BASE_URL}/api/v1/portfolios`, () => {
    const newPortfolio = {
      ...mockPortfolios[0],
      id: Date.now(),
      name: 'Новый портфель',
      total_value: 0,
      daily_change: 0,
      daily_change_percent: 0
    };
    
    return HttpResponse.json(newPortfolio, { status: 201 });
  }),

  // Tax calculation endpoints
  http.post(`${API_BASE_URL}/api/v1/tax/calculate`, () => {
    return HttpResponse.json({
      total_income: 100000,
      total_tax: 13000,
      tax_rate: 0.13,
      deductions: 0,
      net_income: 87000,
      calculation_details: {
        income_sources: [
          {
            type: 'dividends',
            amount: 50000,
            tax: 6500
          },
          {
            type: 'capital_gains',
            amount: 50000,
            tax: 6500
          }
        ]
      }
    });
  }),

  // Analytics endpoints
  http.get(`${API_BASE_URL}/api/v1/analytics/portfolio/:id`, ({ params }) => {
    const { id } = params;
    return HttpResponse.json({
      portfolio_id: parseInt(id as string),
      performance: {
        total_return: 15.5,
        annual_return: 12.3,
        volatility: 18.2,
        sharpe_ratio: 0.68
      },
      allocation: {
        stocks: 60,
        bonds: 30,
        cash: 10
      },
      top_holdings: [
        { symbol: 'SBER', weight: 15.5, value: 232500 },
        { symbol: 'GAZP', weight: 12.3, value: 184500 },
        { symbol: 'LKOH', weight: 10.1, value: 151500 }
      ]
    });
  }),

  // Default fallback for unhandled requests
  http.all('*', ({ request }) => {
    console.warn(`Unhandled ${request.method} request to ${request.url}`);
    return HttpResponse.json(
      { error: 'Not found' },
      { status: 404 }
    );
  })
];

// Create the server instance
export const server = setupServer(...handlers);