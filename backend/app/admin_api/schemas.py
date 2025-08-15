"""
Pydantic schemas for admin API.
"""

from pydantic import BaseModel, Field


class AdminTaskSchema(BaseModel):
    id: str = Field(..., description="Идентификатор задачи")
    title: str
    status: str
    details: str | None = None


class RiskSignalSchema(BaseModel):
    code: str
    severity: str
    message: str
    metadata: dict | None = None


class GithubRepoMetricsSchema(BaseModel):
    repo: str
    lead_time_pr_days: float | None = None
    review_time_hours: float | None = None
    merge_rate: float | None = None
    throughput_per_week: int | None = None
    risk_signals: list[RiskSignalSchema] = []


