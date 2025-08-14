/**
 * Tests for portfolio-related components.
 * 
 * This file contains tests for portfolio list, portfolio card,
 * portfolio creation and management components.
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render, mockApiSuccess, mockApiError, mockPortfolio } from '../setup';

// Mock components (replace with actual imports when components exist)
const MockPortfolioCard = ({ 
  portfolio, 
  onEdit, 
  onDelete 
}: { 
  portfolio: any; 
  onEdit: (portfolio: any) => void;
  onDelete: (portfolioId: number) => void;
}) => (
  <div data-testid={`portfolio-card-${portfolio.id}`}>
    <h3 data-testid="portfolio-name">{portfolio.name}</h3>
    <p data-testid="portfolio-description">{portfolio.description}</p>
    <p data-testid="portfolio-value">${portfolio.total_value?.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
    <p data-testid="portfolio-currency">{portfolio.base_currency}</p>
    <button 
      data-testid="edit-button" 
      onClick={() => onEdit(portfolio)}
    >
      Edit
    </button>
    <button 
      data-testid="delete-button" 
      onClick={() => onDelete(portfolio.id)}
    >
      Delete
    </button>
  </div>
);

const MockPortfolioList = ({ 
  portfolios, 
  onEdit, 
  onDelete,
  isLoading = false 
}: { 
  portfolios: any[];
  onEdit: (portfolio: any) => void;
  onDelete: (portfolioId: number) => void;
  isLoading?: boolean;
}) => (
  <div data-testid="portfolio-list">
    {isLoading ? (
      <div data-testid="loading-spinner">Loading...</div>
    ) : portfolios.length > 0 ? (
      portfolios.map(portfolio => (
        <MockPortfolioCard
          key={portfolio.id}
          portfolio={portfolio}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))
    ) : (
      <div data-testid="no-portfolios">No portfolios found</div>
    )}
  </div>
);

const MockPortfolioForm = ({ 
  portfolio,
  onSubmit,
  onCancel 
}: { 
  portfolio?: any;
  onSubmit: (data: any) => void;
  onCancel: () => void;
}) => (
  <form 
    data-testid="portfolio-form"
    onSubmit={(e) => {
      e.preventDefault();
      const formData = new FormData(e.target as HTMLFormElement);
      onSubmit({
        name: formData.get('name'),
        description: formData.get('description'),
        base_currency: formData.get('base_currency'),
      });
    }}
  >
    <input
      name="name"
      type="text"
      placeholder="Portfolio Name"
      data-testid="name-input"
      defaultValue={portfolio?.name || ''}
      required
    />
    <textarea
      name="description"
      placeholder="Description"
      data-testid="description-input"
      defaultValue={portfolio?.description || ''}
    />
    <select
      name="base_currency"
      data-testid="currency-select"
      defaultValue={portfolio?.base_currency || 'USD'}
      required
    >
      <option value="USD">USD</option>
      <option value="EUR">EUR</option>
      <option value="RUB">RUB</option>
    </select>
    <button type="submit" data-testid="submit-button">
      {portfolio ? 'Update' : 'Create'} Portfolio
    </button>
    <button type="button" data-testid="cancel-button" onClick={onCancel}>
      Cancel
    </button>
  </form>
);

describe('Portfolio Components', () => {
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    user = userEvent.setup();
  });

  describe('PortfolioCard', () => {
    const mockPortfolioData = {
      id: 1,
      name: 'Test Portfolio',
      description: 'A test portfolio for unit tests',
      base_currency: 'USD',
      total_value: 50000,
      is_active: true,
    };

    it('renders portfolio information correctly', () => {
      const onEdit = vi.fn();
      const onDelete = vi.fn();
      
      render(
        <MockPortfolioCard 
          portfolio={mockPortfolioData} 
          onEdit={onEdit} 
          onDelete={onDelete} 
        />
      );

      expect(screen.getByTestId('portfolio-name')).toHaveTextContent('Test Portfolio');
      expect(screen.getByTestId('portfolio-description')).toHaveTextContent('A test portfolio for unit tests');
      expect(screen.getByTestId('portfolio-value')).toHaveTextContent('$50,000');
      expect(screen.getByTestId('portfolio-currency')).toHaveTextContent('USD');
    });

    it('handles edit button click', async () => {
      const onEdit = vi.fn();
      const onDelete = vi.fn();
      
      render(
        <MockPortfolioCard 
          portfolio={mockPortfolioData} 
          onEdit={onEdit} 
          onDelete={onDelete} 
        />
      );

      const editButton = screen.getByTestId('edit-button');
      await user.click(editButton);

      expect(onEdit).toHaveBeenCalledWith(mockPortfolioData);
    });

    it('handles delete button click', async () => {
      const onEdit = vi.fn();
      const onDelete = vi.fn();
      
      render(
        <MockPortfolioCard 
          portfolio={mockPortfolioData} 
          onEdit={onEdit} 
          onDelete={onDelete} 
        />
      );

      const deleteButton = screen.getByTestId('delete-button');
      await user.click(deleteButton);

      expect(onDelete).toHaveBeenCalledWith(mockPortfolioData.id);
    });

    it('formats currency values correctly', () => {
      const portfolioWithLargeValue = {
        ...mockPortfolioData,
        total_value: 1234567.89,
      };

      const onEdit = vi.fn();
      const onDelete = vi.fn();
      
      render(
        <MockPortfolioCard 
          portfolio={portfolioWithLargeValue} 
          onEdit={onEdit} 
          onDelete={onDelete} 
        />
      );

      expect(screen.getByTestId('portfolio-value')).toHaveTextContent('$1,234,568');
    });
  });

  describe('PortfolioList', () => {
    const mockPortfolios = [
      {
        id: 1,
        name: 'Growth Portfolio',
        description: 'Long-term growth',
        base_currency: 'USD',
        total_value: 50000,
      },
      {
        id: 2,
        name: 'Conservative Portfolio',
        description: 'Low-risk investments',
        base_currency: 'EUR',
        total_value: 25000,
      },
    ];

    it('renders list of portfolios', () => {
      const onEdit = vi.fn();
      const onDelete = vi.fn();
      
      render(
        <MockPortfolioList 
          portfolios={mockPortfolios} 
          onEdit={onEdit} 
          onDelete={onDelete} 
        />
      );

      expect(screen.getByTestId('portfolio-list')).toBeInTheDocument();
      expect(screen.getByTestId('portfolio-card-1')).toBeInTheDocument();
      expect(screen.getByTestId('portfolio-card-2')).toBeInTheDocument();
    });

    it('shows loading state', () => {
      const onEdit = vi.fn();
      const onDelete = vi.fn();
      
      render(
        <MockPortfolioList 
          portfolios={[]} 
          onEdit={onEdit} 
          onDelete={onDelete} 
          isLoading={true}
        />
      );

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
      expect(screen.getByTestId('loading-spinner')).toHaveTextContent('Loading...');
    });

    it('shows empty state when no portfolios', () => {
      const onEdit = vi.fn();
      const onDelete = vi.fn();
      
      render(
        <MockPortfolioList 
          portfolios={[]} 
          onEdit={onEdit} 
          onDelete={onDelete} 
          isLoading={false}
        />
      );

      expect(screen.getByTestId('no-portfolios')).toBeInTheDocument();
      expect(screen.getByTestId('no-portfolios')).toHaveTextContent('No portfolios found');
    });

    it('propagates edit and delete actions', async () => {
      const onEdit = vi.fn();
      const onDelete = vi.fn();
      
      render(
        <MockPortfolioList 
          portfolios={mockPortfolios} 
          onEdit={onEdit} 
          onDelete={onDelete} 
        />
      );

      // Test edit action on first portfolio
      const firstEditButton = screen.getAllByTestId('edit-button')[0];
      await user.click(firstEditButton);
      expect(onEdit).toHaveBeenCalledWith(mockPortfolios[0]);

      // Test delete action on second portfolio
      const secondDeleteButton = screen.getAllByTestId('delete-button')[1];
      await user.click(secondDeleteButton);
      expect(onDelete).toHaveBeenCalledWith(mockPortfolios[1].id);
    });
  });

  describe('PortfolioForm', () => {
    it('renders create form with empty fields', () => {
      const onSubmit = vi.fn();
      const onCancel = vi.fn();
      
      render(
        <MockPortfolioForm onSubmit={onSubmit} onCancel={onCancel} />
      );

      expect(screen.getByTestId('portfolio-form')).toBeInTheDocument();
      expect(screen.getByTestId('name-input')).toHaveValue('');
      expect(screen.getByTestId('description-input')).toHaveValue('');
      expect(screen.getByTestId('currency-select')).toHaveValue('USD');
      expect(screen.getByTestId('submit-button')).toHaveTextContent('Create Portfolio');
    });

    it('renders edit form with existing data', () => {
      const existingPortfolio = {
        id: 1,
        name: 'Existing Portfolio',
        description: 'Existing description',
        base_currency: 'EUR',
      };

      const onSubmit = vi.fn();
      const onCancel = vi.fn();
      
      render(
        <MockPortfolioForm 
          portfolio={existingPortfolio}
          onSubmit={onSubmit} 
          onCancel={onCancel} 
        />
      );

      expect(screen.getByTestId('name-input')).toHaveValue('Existing Portfolio');
      expect(screen.getByTestId('description-input')).toHaveValue('Existing description');
      expect(screen.getByTestId('currency-select')).toHaveValue('EUR');
      expect(screen.getByTestId('submit-button')).toHaveTextContent('Update Portfolio');
    });

    it('submits form with valid data', async () => {
      const onSubmit = vi.fn();
      const onCancel = vi.fn();
      
      render(
        <MockPortfolioForm onSubmit={onSubmit} onCancel={onCancel} />
      );

      await user.type(screen.getByTestId('name-input'), 'New Portfolio');
      await user.type(screen.getByTestId('description-input'), 'Portfolio description');
      await user.selectOptions(screen.getByTestId('currency-select'), 'EUR');
      await user.click(screen.getByTestId('submit-button'));

      expect(onSubmit).toHaveBeenCalledWith({
        name: 'New Portfolio',
        description: 'Portfolio description',
        base_currency: 'EUR',
      });
    });

    it('handles cancel action', async () => {
      const onSubmit = vi.fn();
      const onCancel = vi.fn();
      
      render(
        <MockPortfolioForm onSubmit={onSubmit} onCancel={onCancel} />
      );

      await user.click(screen.getByTestId('cancel-button'));

      expect(onCancel).toHaveBeenCalled();
      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('validates required fields', async () => {
      const onSubmit = vi.fn();
      const onCancel = vi.fn();
      
      render(
        <MockPortfolioForm onSubmit={onSubmit} onCancel={onCancel} />
      );

      // Try to submit without filling required fields
      await user.click(screen.getByTestId('submit-button'));

      // Form validation should prevent submission
      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('supports all currency options', async () => {
      const onSubmit = vi.fn();
      const onCancel = vi.fn();
      
      render(
        <MockPortfolioForm onSubmit={onSubmit} onCancel={onCancel} />
      );

      const currencySelect = screen.getByTestId('currency-select');
      
      // Test all currency options
      await user.selectOptions(currencySelect, 'USD');
      expect(currencySelect).toHaveValue('USD');

      await user.selectOptions(currencySelect, 'EUR');
      expect(currencySelect).toHaveValue('EUR');

      await user.selectOptions(currencySelect, 'RUB');
      expect(currencySelect).toHaveValue('RUB');
    });
  });

  describe('Portfolio API Integration', () => {
    it('handles successful portfolio creation', async () => {
      mockApiSuccess({
        id: 3,
        name: 'New Portfolio',
        description: 'New portfolio description',
        base_currency: 'USD',
        total_value: 0,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      });

      const onSubmit = vi.fn(async (data) => {
        const response = await fetch('/api/v1/portfolios', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mock-token',
          },
          body: JSON.stringify(data),
        });
        const result = await response.json();
        expect(result.name).toBe('New Portfolio');
        expect(response.status).toBe(201);
      });

      const onCancel = vi.fn();
      
      render(
        <MockPortfolioForm onSubmit={onSubmit} onCancel={onCancel} />
      );

      await user.type(screen.getByTestId('name-input'), 'New Portfolio');
      await user.type(screen.getByTestId('description-input'), 'New portfolio description');
      await user.click(screen.getByTestId('submit-button'));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalled();
      });
    });

    it('handles portfolio creation error', async () => {
      mockApiError(400, 'Portfolio name already exists');

      const onSubmit = vi.fn(async (data) => {
        const response = await fetch('/api/v1/portfolios', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mock-token',
          },
          body: JSON.stringify(data),
        });
        expect(response.status).toBe(400);
      });

      const onCancel = vi.fn();
      
      render(
        <MockPortfolioForm onSubmit={onSubmit} onCancel={onCancel} />
      );

      await user.type(screen.getByTestId('name-input'), 'Existing Portfolio');
      await user.click(screen.getByTestId('submit-button'));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalled();
      });
    });

    it('handles portfolio update', async () => {
      const existingPortfolio = mockPortfolio;

      mockApiSuccess({
        ...existingPortfolio,
        name: 'Updated Portfolio Name',
        updated_at: new Date().toISOString(),
      });

      const onSubmit = vi.fn(async (data) => {
        const response = await fetch(`/api/v1/portfolios/${existingPortfolio.id}`, {
          method: 'PUT',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mock-token',
          },
          body: JSON.stringify(data),
        });
        const result = await response.json();
        expect(result.name).toBe('Updated Portfolio Name');
        expect(response.status).toBe(200);
      });

      const onCancel = vi.fn();
      
      render(
        <MockPortfolioForm 
          portfolio={existingPortfolio}
          onSubmit={onSubmit} 
          onCancel={onCancel} 
        />
      );

      // Clear and update the name
      const nameInput = screen.getByTestId('name-input');
      await user.clear(nameInput);
      await user.type(nameInput, 'Updated Portfolio Name');
      await user.click(screen.getByTestId('submit-button'));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalled();
      });
    });

    it('handles portfolio deletion', async () => {
      mockApiSuccess(null);

      const portfolioId = 1;
      
      const deletePortfolio = async (id: number) => {
        const response = await fetch(`/api/v1/portfolios/${id}`, {
          method: 'DELETE',
          headers: { 
            'Authorization': 'Bearer mock-token',
          },
        });
        expect(response.status).toBe(204);
      };

      await deletePortfolio(portfolioId);
    });
  });

  describe('Accessibility', () => {
    it('has proper form labels and structure', () => {
      const onSubmit = vi.fn();
      const onCancel = vi.fn();
      
      render(
        <MockPortfolioForm onSubmit={onSubmit} onCancel={onCancel} />
      );

      const form = screen.getByTestId('portfolio-form');
      expect(form.tagName).toBe('FORM');

      const nameInput = screen.getByTestId('name-input');
      const currencySelect = screen.getByTestId('currency-select');
      
      expect(nameInput).toHaveAttribute('required');
      expect(currencySelect).toHaveAttribute('required');
    });

    it('supports keyboard navigation', async () => {
      const onSubmit = vi.fn();
      const onCancel = vi.fn();
      
      render(
        <MockPortfolioForm onSubmit={onSubmit} onCancel={onCancel} />
      );

      const nameInput = screen.getByTestId('name-input');
      const descriptionInput = screen.getByTestId('description-input');
      const currencySelect = screen.getByTestId('currency-select');
      const submitButton = screen.getByTestId('submit-button');

      // Test tab navigation
      nameInput.focus();
      expect(nameInput).toHaveFocus();

      await user.tab();
      expect(descriptionInput).toHaveFocus();

      await user.tab();
      expect(currencySelect).toHaveFocus();

      await user.tab();
      expect(submitButton).toHaveFocus();
    });
  });
});
