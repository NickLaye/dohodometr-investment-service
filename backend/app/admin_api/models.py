"""
Minimal admin module DTOs (ORM-agnostic).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AdminTask:
    id: str
    title: str
    status: str  # pending | running | success | failed
    details: str | None = None


@dataclass
class RiskSignal:
    code: str
    severity: str  # low | medium | high | critical
    message: str
    metadata: dict | None = None


@dataclass
class GithubRepoMetrics:
    repo: str
    lead_time_pr_days: float | None
    review_time_hours: float | None
    merge_rate: float | None
    throughput_per_week: int | None
    risk_signals: list[RiskSignal]


