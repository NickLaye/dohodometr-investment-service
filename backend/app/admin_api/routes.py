"""
Admin module routes (minimal skeleton):
 - /admin/github/metrics
 - /admin/tasks
"""
# ruff: noqa: I001, B008

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.admin_api.github_sync import fetch_github_metrics
from app.admin_api.schemas import AdminTaskSchema, GithubRepoMetricsSchema
from app.core.database_sync import get_db
from app.core.security import get_current_user


router = APIRouter()


@router.get("/github/metrics", response_model=GithubRepoMetricsSchema)
async def github_metrics(
    repo: str = Query(..., description="owner/repo"),
    token: str | None = Query(None, description="GitHub PAT"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ = db  # placeholder for future use
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    metrics = await fetch_github_metrics(repo, token)
    return GithubRepoMetricsSchema(**metrics.__dict__)


@router.get("/tasks", response_model=list[AdminTaskSchema])
def list_tasks(current_user=Depends(get_current_user)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    # Заглушка, для dev-UI
    return [
        AdminTaskSchema(
            id="daily-sync",
            title="Ежедневная синхронизация",
            status="pending",
        )
    ]


