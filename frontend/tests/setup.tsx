/**
 * Test setup configuration for Vitest.
 * 
 * This file configures the testing environment for React components,
 * including mocking APIs, setting up testing libraries, and configuring
 * global test utilities.
 */

import React from 'react'
import '@testing-library/jest-dom';
import { expect, afterEach, beforeAll, afterAll, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import { server } from './mocks/server';

// Extend Vitest's expect with jest-dom matchers
expect.extend({});

// Setup MSW server for API mocking
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

afterEach(() => {
  server.resetHandlers();
  cleanup();
});

afterAll(() => {
  server.close();
});

// Mock Next.js router
vi.mock('next/router', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    pathname: '/',
    query: {},
    asPath: '/',
    route: '/',
  }),
}));

// Mock Next.js navigation (App Router)
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}));

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
process.env.NEXT_PUBLIC_APP_NAME = 'Investment Service';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
});

// Mock IntersectionObserver
const IntersectionObserverMock = vi.fn(() => ({
  disconnect: vi.fn(),
  observe: vi.fn(),
  unobserve: vi.fn(),
}));

Object.defineProperty(window, 'IntersectionObserver', {
  value: IntersectionObserverMock,
});

Object.defineProperty(global, 'IntersectionObserver', {
  value: IntersectionObserverMock,
});

// Mock ResizeObserver
const ResizeObserverMock = vi.fn(() => ({
  disconnect: vi.fn(),
  observe: vi.fn(),
  unobserve: vi.fn(),
}));

Object.defineProperty(window, 'ResizeObserver', {
  value: ResizeObserverMock,
});

// Mock fetch API
global.fetch = vi.fn();

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock requestAnimationFrame
global.requestAnimationFrame = vi.fn(cb => setTimeout(cb, 0));
global.cancelAnimationFrame = vi.fn(id => clearTimeout(id));

// Mock scrollTo
Object.defineProperty(window, 'scrollTo', {
  value: vi.fn(),
  writable: true,
});

// Mock HTMLElement.scrollIntoView
Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
  value: vi.fn(),
  writable: true,
});

// Mock console methods to reduce noise in tests
const consoleMethods = ['log', 'warn', 'error', 'info', 'debug'] as const;
consoleMethods.forEach(method => {
  vi.spyOn(console, method).mockImplementation(() => {});
});

// Global test utilities
export const mockUser = {
  id: 1,
  email: 'test@example.com',
  username: 'testuser',
  full_name: 'Test User',
  is_active: true,
  is_superuser: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockPortfolio = {
  id: 1,
  name: 'Test Portfolio',
  description: 'A test portfolio',
  base_currency: 'USD',
  is_active: true,
  user_id: 1,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockTransaction = {
  id: 1,
  date: '2024-01-15',
  type: 'buy',
  symbol: 'AAPL',
  quantity: 10,
  price: 150.00,
  currency: 'USD',
  commission: 1.00,
  description: 'Buy Apple shares',
  portfolio_id: 1,
  account_id: 1,
  created_at: '2024-01-15T00:00:00Z',
  updated_at: '2024-01-15T00:00:00Z',
};

// Test helper functions
export const createMockResponse = <T>(data: T, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: () => Promise.resolve(data),
  text: () => Promise.resolve(JSON.stringify(data)),
  headers: new Headers(),
  redirected: false,
  statusText: 'OK',
  type: 'basic' as ResponseType,
  url: '',
  clone: vi.fn(),
  body: null,
  bodyUsed: false,
  arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
  blob: () => Promise.resolve(new Blob()),
  formData: () => Promise.resolve(new FormData()),
});

export const mockApiSuccess = <T>(data: T) => {
  (fetch as any).mockResolvedValueOnce(createMockResponse(data));
};

export const mockApiError = (status = 500, message = 'Internal Server Error') => {
  (fetch as any).mockResolvedValueOnce(
    createMockResponse({ error: message }, status)
  );
};

// Helper to create auth context value
export const createMockAuthContext = (user = mockUser) => ({
  user,
  login: vi.fn(),
  logout: vi.fn(),
  register: vi.fn(),
  isLoading: false,
  isAuthenticated: !!user,
  token: 'mock-jwt-token',
});

// Custom render function with providers
import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient;
}

export const customRender = (
  ui: ReactElement,
  {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    }),
    ...renderOptions
  }: CustomRenderOptions = {}
) => {
  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

// Re-export everything from testing-library
export * from '@testing-library/react';
export { customRender as render };
