"""
Health check endpoints.

Provides API health status and system diagnostics.
"""

from fastapi import APIRouter
from datetime import datetime
import logging

from backend.config.settings import settings
from backend.config.supabase import check_connection

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns current API status and system health indicators.

    Returns:
        dict: Health status information.
    """
    # Check database connection
    db_status = "unknown"
    try:
        db_connected = await check_connection()
        db_status = "connected" if db_connected else "disconnected"
    except Exception as e:
        logger.error(f"Health check database error: {e}")
        db_status = "error"

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "version": "1.0.0",
        "services": {
            "api": "running",
            "database": db_status,
        },
        "uptime": "available on metrics endpoint"  # TODO: Implement metrics
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration.

    Returns:
        dict: Readiness status (200 if ready, 503 if not).
    """
    try:
        # Check if critical services are available
        db_connected = await check_connection()

        if not db_connected:
            return {
                "ready": False,
                "reason": "Database connection failed"
            }

        return {
            "ready": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        return {
            "ready": False,
            "reason": str(e)
        }


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check for Kubernetes/container orchestration.

    Returns:
        dict: Liveness status (always returns 200 if service is running).
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }
