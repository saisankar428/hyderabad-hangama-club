"""Storage utility tests."""

import pytest

from src.infrastructure.storage import StorageError, get_public_url, validate_image_upload


def test_validate_image_upload_ok():
    ext = validate_image_upload("image/png", 1024)
    assert ext == ".png"


def test_validate_image_upload_rejects_type():
    with pytest.raises(StorageError):
        validate_image_upload("application/pdf", 1024)


def test_validate_image_upload_rejects_size():
    with pytest.raises(StorageError):
        validate_image_upload("image/jpeg", 6 * 1024 * 1024)


def test_get_public_url_format(monkeypatch):
    from src.core.config import settings

    monkeypatch.setattr(settings, "SUPABASE_URL", "https://abc.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_STORAGE_BUCKET", "payment-screenshots")

    url = get_public_url("screenshots/test.jpg")
    assert url == "https://abc.supabase.co/storage/v1/object/public/payment-screenshots/screenshots/test.jpg"
