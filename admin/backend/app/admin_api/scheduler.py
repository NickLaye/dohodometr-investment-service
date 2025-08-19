from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.db import SessionLocal
from .github_sync import sync_github


def _job_sync_github() -> None:
    settings = get_settings()
    if not settings.gh_token or not settings.repo:
        return
    db: Session = SessionLocal()
    try:
        sync_github(settings.gh_token, settings.repo, db)
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(_job_sync_github, "interval", minutes=10, id="sync_github", replace_existing=True)
    scheduler.start()
    return scheduler


