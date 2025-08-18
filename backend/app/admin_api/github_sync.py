"""
GitHub sync placeholder (metrics/KPI, tasks backups).
"""

from app.admin_api.models import GithubRepoMetrics, RiskSignal


async def fetch_github_metrics(repo: str, token: str | None) -> GithubRepoMetrics:
    """Возвращает базовые метрики (заглушка, если нет токена)."""
    if not (repo and token):
        return GithubRepoMetrics(
            repo=repo,
            lead_time_pr_days=None,
            review_time_hours=None,
            merge_rate=None,
            throughput_per_week=None,
            risk_signals=[],
        )

    # TODO: Реальная интеграция через GitHub API v4 (GraphQL) или v3 (REST)
    return GithubRepoMetrics(
        repo=repo,
        lead_time_pr_days=1.7,
        review_time_hours=5.3,
        merge_rate=0.86,
        throughput_per_week=12,
        risk_signals=[
            RiskSignal(code="stale_pr", severity="low", message="Есть PR > 14 дней"),
        ],
    )


