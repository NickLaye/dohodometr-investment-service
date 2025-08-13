"""
Основной роутер API v1 для сервиса учета инвестиций.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, portfolios, transactions, analytics, tax_calculator

api_router = APIRouter()

# Включаем роутеры для различных модулей
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["Portfolios"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(tax_calculator.router, prefix="/tax", tags=["Tax Calculator"])

# Базовая информация об API
@api_router.get("/", tags=["Root"])
async def api_info():
    """Информация об API v1."""
    return {
        "message": "Investment Service API v1",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth",
            "portfolios": "/portfolios", 
            "transactions": "/transactions",
            "analytics": "/analytics",
            "tax": "/tax"
        }
    }
