"""
Pydantic-схемы для портфелей, используемые в репозитории и тестах.
"""

from typing import Optional
from pydantic import BaseModel, validator


class PortfolioBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_currency: str = "USD"

    @validator("name")
    def validate_name(cls, v: str) -> str:
        if v is None or not v.strip():
            raise ValueError("name must not be empty")
        if len(v) > 255:
            raise ValueError("name is too long")
        return v.strip()

    @validator("base_currency")
    def validate_currency(cls, v: str) -> str:
        if v is None:
            raise ValueError("base_currency is required")
        v = v.strip().upper()
        if len(v) != 3 or not v.isalpha():
            raise ValueError("base_currency must be a 3-letter ISO code")
        return v


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    @validator("name")
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.strip():
            raise ValueError("name must not be empty")
        if len(v) > 255:
            raise ValueError("name is too long")
        return v.strip()


