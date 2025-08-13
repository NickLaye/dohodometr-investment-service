"""
Unit tests for portfolio functionality.

Tests cover:
- Portfolio creation and management
- Portfolio analytics and calculations
- Portfolio permissions and access control
- Portfolio data validation
"""
import pytest
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import patch, MagicMock

from app.repositories.portfolio import PortfolioRepository
from app.services.portfolio_analytics import PortfolioAnalyticsService
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate


class TestPortfolioRepository:
    """Test portfolio repository functionality."""
    
    def test_create_portfolio(self, db_session, mock_user):
        """Test portfolio creation."""
        portfolio_repo = PortfolioRepository(db_session)
        portfolio_data = PortfolioCreate(
            name="Test Portfolio",
            description="A test portfolio",
            base_currency="USD"
        )
        
        portfolio = portfolio_repo.create(portfolio_data, user_id=mock_user["id"])
        
        assert portfolio.name == portfolio_data.name
        assert portfolio.description == portfolio_data.description
        assert portfolio.base_currency == portfolio_data.base_currency
        assert portfolio.user_id == mock_user["id"]
        assert portfolio.is_active is True
        assert portfolio.created_at is not None
    
    def test_get_portfolio_by_id(self, db_session, mock_user):
        """Test getting portfolio by ID."""
        portfolio_repo = PortfolioRepository(db_session)
        
        # Create portfolio
        portfolio_data = PortfolioCreate(
            name="Test Portfolio",
            description="A test portfolio",
            base_currency="USD"
        )
        created_portfolio = portfolio_repo.create(portfolio_data, user_id=mock_user["id"])
        
        # Retrieve portfolio
        found_portfolio = portfolio_repo.get_by_id(created_portfolio.id)
        
        assert found_portfolio is not None
        assert found_portfolio.id == created_portfolio.id
        assert found_portfolio.name == portfolio_data.name
    
    def test_get_user_portfolios(self, db_session, mock_user):
        """Test getting all portfolios for a user."""
        portfolio_repo = PortfolioRepository(db_session)
        
        # Create multiple portfolios
        portfolio1_data = PortfolioCreate(
            name="Portfolio 1",
            base_currency="USD"
        )
        portfolio2_data = PortfolioCreate(
            name="Portfolio 2",
            base_currency="EUR"
        )
        
        portfolio1 = portfolio_repo.create(portfolio1_data, user_id=mock_user["id"])
        portfolio2 = portfolio_repo.create(portfolio2_data, user_id=mock_user["id"])
        
        # Get user portfolios
        user_portfolios = portfolio_repo.get_by_user_id(mock_user["id"])
        
        assert len(user_portfolios) == 2
        portfolio_names = [p.name for p in user_portfolios]
        assert "Portfolio 1" in portfolio_names
        assert "Portfolio 2" in portfolio_names
    
    def test_update_portfolio(self, db_session, mock_user):
        """Test portfolio update."""
        portfolio_repo = PortfolioRepository(db_session)
        
        # Create portfolio
        portfolio_data = PortfolioCreate(
            name="Original Name",
            description="Original description",
            base_currency="USD"
        )
        portfolio = portfolio_repo.create(portfolio_data, user_id=mock_user["id"])
        
        # Update portfolio
        update_data = PortfolioUpdate(
            name="Updated Name",
            description="Updated description"
        )
        updated_portfolio = portfolio_repo.update(portfolio.id, update_data)
        
        assert updated_portfolio.name == "Updated Name"
        assert updated_portfolio.description == "Updated description"
        assert updated_portfolio.base_currency == "USD"  # Unchanged
        assert updated_portfolio.updated_at > portfolio.created_at
    
    def test_delete_portfolio(self, db_session, mock_user):
        """Test portfolio deletion (soft delete)."""
        portfolio_repo = PortfolioRepository(db_session)
        
        # Create portfolio
        portfolio_data = PortfolioCreate(
            name="Portfolio to Delete",
            base_currency="USD"
        )
        portfolio = portfolio_repo.create(portfolio_data, user_id=mock_user["id"])
        
        # Delete portfolio
        deleted = portfolio_repo.delete(portfolio.id)
        
        assert deleted is True
        
        # Portfolio should not be found in active portfolios
        found_portfolio = portfolio_repo.get_by_id(portfolio.id)
        assert found_portfolio is None or found_portfolio.is_active is False


class TestPortfolioAnalytics:
    """Test portfolio analytics calculations."""
    
    @pytest.fixture
    def analytics_service(self, db_session):
        """Create analytics service instance."""
        return PortfolioAnalyticsService(db_session)
    
    def test_calculate_portfolio_value(self, analytics_service):
        """Test portfolio total value calculation."""
        # Mock portfolio with holdings
        mock_holdings = [
            {"symbol": "AAPL", "quantity": 10, "current_price": 150.00},
            {"symbol": "GOOGL", "quantity": 5, "current_price": 2800.00},
            {"symbol": "MSFT", "quantity": 8, "current_price": 300.00},
        ]
        
        with patch.object(analytics_service, 'get_portfolio_holdings') as mock_holdings_method:
            mock_holdings_method.return_value = mock_holdings
            
            total_value = analytics_service.calculate_portfolio_value(portfolio_id=1)
            
            expected_value = (10 * 150.00) + (5 * 2800.00) + (8 * 300.00)
            assert total_value == expected_value
    
    def test_calculate_portfolio_allocation(self, analytics_service):
        """Test portfolio asset allocation calculation."""
        mock_holdings = [
            {"symbol": "AAPL", "value": 1500.00, "sector": "Technology"},
            {"symbol": "GOOGL", "value": 14000.00, "sector": "Technology"},
            {"symbol": "JNJ", "value": 2000.00, "sector": "Healthcare"},
            {"symbol": "XOM", "value": 1000.00, "sector": "Energy"},
        ]
        
        with patch.object(analytics_service, 'get_portfolio_holdings') as mock_holdings_method:
            mock_holdings_method.return_value = mock_holdings
            
            allocation = analytics_service.calculate_allocation_by_sector(portfolio_id=1)
            
            total_value = 18500.00
            expected_allocation = {
                "Technology": round((15500.00 / total_value) * 100, 2),
                "Healthcare": round((2000.00 / total_value) * 100, 2),
                "Energy": round((1000.00 / total_value) * 100, 2),
            }
            
            assert allocation == expected_allocation
    
    def test_calculate_portfolio_performance(self, analytics_service):
        """Test portfolio performance calculation."""
        # Mock historical data
        mock_historical_data = [
            {"date": date(2024, 1, 1), "value": 10000.00},
            {"date": date(2024, 6, 1), "value": 11000.00},
            {"date": date(2024, 12, 1), "value": 12000.00},
        ]
        
        with patch.object(analytics_service, 'get_portfolio_historical_values') as mock_method:
            mock_method.return_value = mock_historical_data
            
            performance = analytics_service.calculate_performance(
                portfolio_id=1,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 1)
            )
            
            expected_return = ((12000.00 - 10000.00) / 10000.00) * 100
            assert performance["total_return"] == expected_return
            assert performance["start_value"] == 10000.00
            assert performance["end_value"] == 12000.00
    
    @patch('app.services.portfolio_analytics.calculate_xirr')
    def test_calculate_xirr(self, mock_xirr, analytics_service):
        """Test XIRR calculation."""
        mock_xirr.return_value = 0.15  # 15% annual return
        
        # Mock cash flows
        mock_cash_flows = [
            {"date": date(2024, 1, 1), "amount": -10000.00},  # Initial investment
            {"date": date(2024, 6, 1), "amount": -5000.00},   # Additional investment
            {"date": date(2024, 12, 1), "amount": 18000.00},  # Final value
        ]
        
        with patch.object(analytics_service, 'get_portfolio_cash_flows') as mock_method:
            mock_method.return_value = mock_cash_flows
            
            xirr = analytics_service.calculate_xirr(portfolio_id=1)
            
            assert xirr == 15.0  # Converted to percentage
            mock_xirr.assert_called_once()


class TestPortfolioValidation:
    """Test portfolio data validation."""
    
    def test_valid_portfolio_creation(self):
        """Test creating portfolio with valid data."""
        portfolio_data = PortfolioCreate(
            name="Valid Portfolio",
            description="A valid portfolio description",
            base_currency="USD"
        )
        
        # Should not raise any validation errors
        assert portfolio_data.name == "Valid Portfolio"
        assert portfolio_data.base_currency == "USD"
    
    def test_invalid_currency_code(self):
        """Test portfolio creation with invalid currency."""
        with pytest.raises(ValueError):
            PortfolioCreate(
                name="Invalid Portfolio",
                base_currency="INVALID"  # Should be 3-letter ISO code
            )
    
    def test_empty_portfolio_name(self):
        """Test portfolio creation with empty name."""
        with pytest.raises(ValueError):
            PortfolioCreate(
                name="",  # Empty name should be invalid
                base_currency="USD"
            )
    
    def test_portfolio_name_too_long(self):
        """Test portfolio creation with name too long."""
        long_name = "x" * 256  # Assuming max length is 255
        
        with pytest.raises(ValueError):
            PortfolioCreate(
                name=long_name,
                base_currency="USD"
            )


@pytest.mark.integration
class TestPortfolioIntegration:
    """Integration tests for portfolio functionality."""
    
    def test_portfolio_crud_flow(self, client, auth_headers):
        """Test complete portfolio CRUD flow."""
        # Create portfolio
        portfolio_data = {
            "name": "Integration Test Portfolio",
            "description": "Portfolio for integration testing",
            "base_currency": "USD"
        }
        
        create_response = client.post(
            "/api/v1/portfolios/",
            json=portfolio_data,
            headers=auth_headers
        )
        
        assert create_response.status_code == 201
        created_portfolio = create_response.json()
        portfolio_id = created_portfolio["id"]
        
        # Read portfolio
        get_response = client.get(
            f"/api/v1/portfolios/{portfolio_id}",
            headers=auth_headers
        )
        
        assert get_response.status_code == 200
        portfolio = get_response.json()
        assert portfolio["name"] == portfolio_data["name"]
        
        # Update portfolio
        update_data = {
            "name": "Updated Portfolio Name",
            "description": "Updated description"
        }
        
        update_response = client.put(
            f"/api/v1/portfolios/{portfolio_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert update_response.status_code == 200
        updated_portfolio = update_response.json()
        assert updated_portfolio["name"] == update_data["name"]
        
        # Delete portfolio
        delete_response = client.delete(
            f"/api/v1/portfolios/{portfolio_id}",
            headers=auth_headers
        )
        
        assert delete_response.status_code == 204
        
        # Verify deletion
        get_deleted_response = client.get(
            f"/api/v1/portfolios/{portfolio_id}",
            headers=auth_headers
        )
        
        assert get_deleted_response.status_code == 404
    
    def test_portfolio_access_control(self, client, auth_headers):
        """Test portfolio access control between users."""
        # Create portfolio with first user
        portfolio_data = {
            "name": "Private Portfolio",
            "base_currency": "USD"
        }
        
        create_response = client.post(
            "/api/v1/portfolios/",
            json=portfolio_data,
            headers=auth_headers
        )
        
        assert create_response.status_code == 201
        portfolio_id = create_response.json()["id"]
        
        # Try to access with different user (if implemented)
        # This would require creating another user and auth headers
        # For now, just test with invalid auth
        
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        
        access_response = client.get(
            f"/api/v1/portfolios/{portfolio_id}",
            headers=invalid_headers
        )
        
        assert access_response.status_code == 401
    
    def test_portfolio_list_pagination(self, client, auth_headers):
        """Test portfolio listing with pagination."""
        # Create multiple portfolios
        portfolios = []
        for i in range(5):
            portfolio_data = {
                "name": f"Portfolio {i+1}",
                "base_currency": "USD"
            }
            
            response = client.post(
                "/api/v1/portfolios/",
                json=portfolio_data,
                headers=auth_headers
            )
            
            assert response.status_code == 201
            portfolios.append(response.json())
        
        # Test listing with pagination
        list_response = client.get(
            "/api/v1/portfolios/?skip=0&limit=3",
            headers=auth_headers
        )
        
        assert list_response.status_code == 200
        portfolio_list = list_response.json()
        
        # Should return first 3 portfolios
        assert len(portfolio_list) <= 3
        
        # Test second page
        list_response_2 = client.get(
            "/api/v1/portfolios/?skip=3&limit=3",
            headers=auth_headers
        )
        
        assert list_response_2.status_code == 200
        portfolio_list_2 = list_response_2.json()
        
        # Should return remaining portfolios
        assert len(portfolio_list_2) <= 2
