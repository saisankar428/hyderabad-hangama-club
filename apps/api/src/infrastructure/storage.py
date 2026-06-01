"""
Supabase Storage adapter for payment screenshots and other uploads.

Public API:
  upload_file(path, data, content_type) -> public HTTPS URL
  delete_file(path) -> None
  get_public_url(path) -> public HTTPS URL
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)

_ALLOWED_IMAGE_TYPES = frozenset({"image/jpeg", "image/png", "image/webp", "image/gif"})
_MAX_BYTES = 5 * 1024 * 1024
_EXT_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

_LOCAL_SCREENSHOTS_DIR = Path("uploads") / "screenshots"


class StorageError(Exception):
    """Raised when a storage operation fails."""


class StorageNotConfiguredError(StorageError):
    """Raised when Supabase Storage is required but not configured."""


def validate_image_upload(content_type: str | None, size: int) -> str:
    """Validate image type and size; return file extension."""
    if content_type not in _ALLOWED_IMAGE_TYPES:
        raise StorageError("Screenshot must be a JPEG, PNG, WEBP, or GIF image")
    if size > _MAX_BYTES:
        raise StorageError("Screenshot must be under 5 MB")
    return _EXT_BY_TYPE.get(content_type or "", ".jpg")


def get_public_url(object_path: str) -> str:
    """Build the public URL for an object in the configured Supabase bucket."""
    path = object_path.lstrip("/")
    base = settings.supabase_url_normalized()
    bucket = settings.SUPABASE_STORAGE_BUCKET
    return f"{base}/storage/v1/object/public/{bucket}/{path}"


def _auth_headers() -> dict[str, str]:
    key = settings.supabase_service_role_key.get_secret_value()
    return {
        "Authorization": f"Bearer {key}",
        "apikey": key,
    }


async def upload_file(object_path: str, data: bytes, content_type: str) -> str:
    """
    Upload bytes to Supabase Storage.

    Returns the public HTTPS URL of the uploaded object.
    """
    if not settings.supabase_configured():
        raise StorageNotConfiguredError(
            "Supabase Storage is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )

    path = object_path.lstrip("/")
    url = f"{settings.supabase_url_normalized()}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{path}"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                content=data,
                headers={
                    **_auth_headers(),
                    "Content-Type": content_type,
                    "x-upsert": "true",
                },
            )
            if response.status_code not in (200, 201):
                logger.error(
                    "Supabase upload failed: status=%s body=%s path=%s",
                    response.status_code,
                    response.text[:500],
                    path,
                )
                raise StorageError(
                    "Unable to save your payment screenshot. Please try again in a few minutes."
                )
    except httpx.HTTPError as exc:
        logger.exception("Supabase upload HTTP error for path=%s", path)
        raise StorageError(
            "Unable to save your payment screenshot. Please try again in a few minutes."
        ) from exc

    public_url = get_public_url(path)
    logger.info("Uploaded object to Supabase Storage: %s", path)
    return public_url


async def delete_file(object_path: str) -> None:
    """Delete an object from Supabase Storage (no-op if storage is not configured)."""
    if not settings.supabase_configured():
        logger.warning("delete_file skipped — Supabase Storage not configured")
        return

    path = object_path.lstrip("/")
    url = f"{settings.supabase_url_normalized()}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{path}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(url, headers=_auth_headers())
            if response.status_code not in (200, 204, 404):
                logger.warning(
                    "Supabase delete unexpected status=%s path=%s body=%s",
                    response.status_code,
                    path,
                    response.text[:300],
                )
    except httpx.HTTPError:
        logger.exception("Supabase delete failed for path=%s", path)


async def _upload_local_fallback(data: bytes, ext: str) -> str:
    """Development-only fallback when Supabase is not configured."""
    _LOCAL_SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    (_LOCAL_SCREENSHOTS_DIR / filename).write_bytes(data)
    logger.warning(
        "Stored screenshot on local disk (dev only): %s — configure Supabase for production",
        filename,
    )
    return f"/uploads/screenshots/{filename}"


async def upload_payment_screenshot(data: bytes, content_type: str, ext: str) -> str:
    """
    Upload a payment screenshot and return a URL stored in the database.

    Production: public Supabase Storage HTTPS URL.
    Development: Supabase if configured, else local /uploads path (requires StaticFiles mount).
    """
    object_path = f"screenshots/{uuid.uuid4().hex}{ext}"

    if settings.supabase_configured():
        return await upload_file(object_path, data, content_type)

    if settings.is_production:
        raise StorageNotConfiguredError(
            "Payment screenshot storage is not configured for production. "
            "Set SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and SUPABASE_STORAGE_BUCKET."
        )

    return await _upload_local_fallback(data, ext)
