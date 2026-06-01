"""Health check endpoints for monitoring and load balancer probes."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db

router = APIRouter(tags=["health"])


def _health_payload() -> dict:
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health", summary="Basic health check")
async def health_check() -> dict:
    """Render / load balancer probe — GET /health"""
    return _health_payload()


@router.get("/health/", summary="Basic health check (trailing slash)")
async def health_check_slash() -> dict:
    return _health_payload()


@router.get("/health/db", summary="Database connectivity check")
async def database_health(db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "pool": "null" if settings.DB_USE_NULL_POOL else "queued",
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": "Database is temporarily unavailable. Please try again shortly.",
            "detail": str(exc) if settings.DEBUG else None,
        }
