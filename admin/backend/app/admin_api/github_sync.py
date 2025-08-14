from __future__ import annotations

from datetime import datetime
from typing import Any

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import PullRequest


def _gh_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "dohodometr-admin-sync",
    }


def sync_github(token: str, repo: str, db: Session) -> dict[str, Any]:
    base = f"https://api.github.com/repos/{repo}"

    # PRs
    prs_resp = requests.get(f"{base}/pulls?state=all&per_page=100", headers=_gh_headers(token), timeout=30)
    prs_resp.raise_for_status()
    updated = 0
    for item in prs_resp.json():
        number = int(item["number"])
        existing = db.execute(select(PullRequest).where(PullRequest.number == number)).scalar_one_or_none()
        created_at = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
        merged_at = (
            datetime.fromisoformat(item["merged_at"].replace("Z", "+00:00")) if item.get("merged_at") else None
        )
        status = "merged" if merged_at else ("open" if item["state"] == "open" else "closed")
        if existing:
            existing.title = item["title"]
            existing.status = status
            existing.created_at = created_at
            existing.merged_at = merged_at
            db.add(existing)
        else:
            db.add(
                PullRequest(
                    number=number,
                    title=item["title"],
                    status=status,
                    created_at=created_at,
                    merged_at=merged_at,
                )
            )
        updated += 1
    db.commit()
    return {"prs_processed": updated}


