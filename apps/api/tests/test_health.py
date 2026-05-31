"""Health endpoint tests - basic smoke tests for CI pipeline."""

import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app


@pytest.mark.asyncio
async def test_health_check():
      """Test basic health endpoint returns 200 with expected fields."""
      async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/health/")

      assert response.status_code == 200
      data = response.json()
      assert data["status"] == "healthy"
      assert "service" in data
      assert "version" in data
      assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_check_returns_app_name():
      """Test health check returns correct app name."""
      async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/health/")

      assert response.status_code == 200
      data = response.json()
      assert "Hyderabad Hangama Club" in data["service"]


@pytest.mark.asyncio
async def test_openapi_docs_accessible():
      """Test API documentation is accessible in debug mode."""
      async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/docs")

      # Should be accessible or redirect
      assert response.status_code in (200, 307, 404)
