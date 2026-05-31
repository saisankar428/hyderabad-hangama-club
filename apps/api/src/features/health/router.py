"""Health check endpoints for monitoring and load balancer probes."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db

router = APIRouter(prefix="/health")


@router.get("/", summary="Basic health check")
async def health_check() -> dict:
      """Returns service status and basic info."""
      return {
          "status": "healthy",
          "service": settings.APP_NAME,
          "version": "1.0.0",
          "environment": settings.APP_ENV,
          "timestamp": datetime.now(timezone.utc).isoformat(),
      }


@router.get("/db", summary="Database connectivity check")
async def database_health(db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
      """Verify database connectivity."""
      try:
                await db.execute(text("SELECT 1"))
                return {"status": "healthy", "database": "connected"}
except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
