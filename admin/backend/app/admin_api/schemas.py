from __future__ import annotations

from datetime import datetime, date
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class AgentIn(BaseModel):
    name: str
    role: str


class AgentOut(BaseModel):
    id: int
    name: str
    role: str
    status: str
    created_at: datetime
    
    model_config = {"from_attributes": True}


class TaskIn(BaseModel):
    title: str
    description: str | None = None
    assignee_id: int | None = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: str | None
    status: str
    assignee_id: int | None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class RiskIn(BaseModel):
    title: str
    level: RiskLevel


class RiskOut(BaseModel):
    id: int
    title: str
    level: RiskLevel
    status: str
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ReportOut(BaseModel):
    id: int
    kind: str
    date: date | None
    data: dict[str, Any]
    is_public: bool
    
    model_config = {"from_attributes": True}


