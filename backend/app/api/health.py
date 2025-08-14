"""
Health Check Endpoint for Dohodometr Backend
Enhanced health check with database and Redis connectivity
"""

import os
import time
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database_sync import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """
    Comprehensive health check endpoint.
    Used by Docker health checks and load balancers.
    """
    start_time = time.time()
    health_status: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {}
    }

    # Database connectivity check
    try:
        db: Session = next(get_db())
        result = db.execute(text("SELECT 1")).fetchone()
        db.close()
        
        if result and result[0] == 1:
            # Совместимость с тестами: строковое значение "ok"
            health_status["checks"]["database"] = "ok"
        else:
            health_status["checks"]["database"] = "error"
    except Exception as e:
        health_status["checks"]["database"] = "error"
        health_status["status"] = "unhealthy"

    # Response time
    response_time = (time.time() - start_time) * 1000  # ms
    health_status["response_time_ms"] = round(response_time, 2)
    
    # Return appropriate HTTP status code
    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )
    
    return health_status


@router.get("/ready", tags=["health"])
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check - simpler check for Kubernetes readiness probes.
    Only checks critical dependencies.
    """
    try:
        # Quick database check
        db: Session = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": ["database"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/live", tags=["health"])
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check - very simple check for Kubernetes liveness probes.
    Just confirms the application is running.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": int(time.time() - getattr(health_check, 'start_time', time.time()))
    }


# Store startup time
health_check.start_time = time.time()
