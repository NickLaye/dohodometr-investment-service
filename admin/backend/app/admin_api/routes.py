from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.security import admin_auth
from .models import Agent, Task, PullRequest, Report, Risk
from .schemas import TaskIn, TaskOut, RiskIn, RiskOut, ReportOut


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(admin_auth)])


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)) -> dict[str, Any]:
    total_agents = db.scalar(select(func.count(Agent.id))) or 0
    open_tasks = db.scalar(select(func.count(Task.id)).where(Task.status == "open")) or 0
    prs_open = db.scalar(select(func.count(PullRequest.id)).where(PullRequest.status == "open")) or 0
    risks_open = db.scalar(select(func.count(Risk.id)).where(Risk.status == "open")) or 0
    return {
        "agents": total_agents,
        "tasks_open": open_tasks,
        "prs_open": prs_open,
        "risks_open": risks_open,
    }


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    role: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = select(Task)
    if status:
        query = query.where(Task.status == status)
    if role:
        query = query.join(Task.assignee).where(Agent.role == role)
    rows = db.execute(query.order_by(Task.created_at.desc())).scalars().all()
    return rows


@router.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(payload: TaskIn, db: Session = Depends(get_db)):
    task = Task(title=payload.title, description=payload.description, assignee_id=payload.assignee_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/prs")
def list_prs(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.execute(select(PullRequest).order_by(PullRequest.created_at.desc())).scalars().all()
    return [
        {
            "id": pr.id,
            "number": pr.number,
            "title": pr.title,
            "status": pr.status,
            "created_at": pr.created_at,
            "merged_at": pr.merged_at,
        }
        for pr in rows
    ]


@router.get("/reports", response_model=list[ReportOut])
def list_reports(
    kind: str | None = Query(default=None),
    date_param: date | None = Query(alias="date", default=None),
    db: Session = Depends(get_db),
):
    query = select(Report)
    if kind:
        query = query.where(Report.kind == kind)
    if date_param:
        query = query.where(Report.date == date_param)
    return db.execute(query.order_by(Report.id.desc())).scalars().all()


@router.get("/risks", response_model=list[RiskOut])
def list_risks(db: Session = Depends(get_db)):
    return db.execute(select(Risk).order_by(Risk.created_at.desc())).scalars().all()


@router.post("/risks", response_model=RiskOut, status_code=201)
def create_risk(payload: RiskIn, db: Session = Depends(get_db)):
    risk = Risk(title=payload.title, level=payload.level.value)
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk


@router.get("/risks/{risk_id}", response_model=RiskOut)
def get_risk(risk_id: int, db: Session = Depends(get_db)):
    risk = db.get(Risk, risk_id)
    if not risk:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Risk not found", "details": {}})
    return risk


@router.put("/risks/{risk_id}", response_model=RiskOut)
def update_risk(risk_id: int, payload: RiskIn, db: Session = Depends(get_db)):
    risk = db.get(Risk, risk_id)
    if not risk:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Risk not found", "details": {}})
    risk.title = payload.title
    risk.level = payload.level.value
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk


@router.delete("/risks/{risk_id}", status_code=204)
def delete_risk(risk_id: int, db: Session = Depends(get_db)):
    risk = db.get(Risk, risk_id)
    if not risk:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Risk not found", "details": {}})
    db.delete(risk)
    db.commit()
    return None


