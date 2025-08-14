from typing import Optional
from pydantic import BaseModel, Field, validator


class PortfolioBase(BaseModel):
	name: str = Field(..., min_length=1, max_length=255)
	description: Optional[str] = None
	base_currency: str = Field(..., min_length=3, max_length=3)

	@validator("base_currency")
	def validate_currency(cls, v: str) -> str:
		if len(v) != 3 or not v.isalpha():
			raise ValueError("Invalid currency code")
		return v.upper()


class PortfolioCreate(PortfolioBase):
	pass


class PortfolioUpdate(BaseModel):
	name: Optional[str] = Field(None, min_length=1, max_length=255)
	description: Optional[str] = None
