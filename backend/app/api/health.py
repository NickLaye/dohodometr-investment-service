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
    health_status = {
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
            health_status["checks"]["database"] = {
                "status": "healthy",
                "details": "PostgreSQL connection successful"
            }
        else:
            health_status["checks"]["database"] = {
                "status": "unhealthy", 
                "details": "Database query returned unexpected result"
            }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "details": f"Database connection failed: {str(e)}"
        }
        health_status["status"] = "unhealthy"

    # Redis connectivity check (if configured)
    try:
        import redis
        redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
        redis_port = getattr(settings, 'REDIS_PORT', 6379)
        redis_db = getattr(settings, 'REDIS_DB', 0)
        
        redis_client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            db=redis_db,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        
        redis_client.ping()
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "details": "Redis connection successful"
        }
        redis_client.close()
        
    except ImportError:
        health_status["checks"]["redis"] = {
            "status": "not_configured",
            "details": "Redis client not installed"
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "details": f"Redis connection failed: {str(e)}"
        }
        # Redis failure is not critical for basic functionality
        # health_status["status"] = "degraded"

    # File system check
    try:
        # Check if we can write to temp directory
        temp_file = "/tmp/health_check_test"
        with open(temp_file, "w") as f:
            f.write("test")
        os.remove(temp_file)
        
        health_status["checks"]["filesystem"] = {
            "status": "healthy",
            "details": "File system write successful"
        }
    except Exception as e:
        health_status["checks"]["filesystem"] = {
            "status": "unhealthy",
            "details": f"File system check failed: {str(e)}"
        }

    # Memory check (basic)
    try:
        import psutil
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        if memory_usage < 90:
            health_status["checks"]["memory"] = {
                "status": "healthy",
                "details": f"Memory usage: {memory_usage:.1f}%"
            }
        else:
            health_status["checks"]["memory"] = {
                "status": "warning",
                "details": f"High memory usage: {memory_usage:.1f}%"
            }
    except ImportError:
        health_status["checks"]["memory"] = {
            "status": "not_available", 
            "details": "psutil not installed"
        }
    except Exception as e:
        health_status["checks"]["memory"] = {
            "status": "error",
            "details": f"Memory check failed: {str(e)}"
        }

    # Response time
    response_time = (time.time() - start_time) * 1000  # ms
    health_status["response_time_ms"] = round(response_time, 2)
    
    # Overall status determination
    failed_checks = [
        check for check in health_status["checks"].values() 
        if check["status"] == "unhealthy"
    ]
    
    if failed_checks:
        health_status["status"] = "unhealthy"
        
    # Warning checks
    warning_checks = [
        check for check in health_status["checks"].values()
        if check["status"] == "warning"
    ]
    
    if warning_checks and health_status["status"] == "healthy":
        health_status["status"] = "degraded"

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
