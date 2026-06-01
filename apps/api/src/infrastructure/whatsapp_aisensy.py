"""
WhatsApp infrastructure - AiSensy integration for ticket delivery.
Infrastructure layer: external service adapter.

AiSensy template params mapping:
  {{1}} → attendee name
  {{2}} → ticket ID / code
Media attachment → QR code image (requires publicly accessible URL via API_BASE_URL).
"""

import asyncio
import logging
from typing import Optional

import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)

_AISENSY_API_URL = "https://backend.aisensy.com/campaign/t1/api/v2"
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.0  # seconds; doubles each attempt: 1s → 2s → 4s


async def send_ticket_whatsapp(
    phone: str,
    name: str,
    ticket_code: str,
    qr_media_url: Optional[str] = None,
) -> None:
    """
    Send WhatsApp booking confirmation via AiSensy.

    Args:
        phone: Attendee phone in E.164 (+919876543210) or 10-digit local format.
        name: Attendee name for the template greeting.
        ticket_code: Unique ticket identifier (e.g. HHC-000042).
        qr_media_url: Publicly accessible HTTPS URL of the QR code image.
                      Omit if no public URL is available — message sends without media.

    Raises:
        RuntimeError: After all retry attempts are exhausted.
    """
    normalized_phone = _normalize_phone(phone)

    payload: dict = {
        "apiKey": settings.AISENSY_API_KEY,
        "campaignName": settings.AISENSY_CAMPAIGN_NAME,
        "destination": normalized_phone,
        "userName": name,
        "templateParams": [name, ticket_code],
        "source": "ticketing-system",
        "buttons": [],
        "carouselCards": [],
        "location": {},
        "paramsFallbackValue": {"FirstName": name},
    }

    if qr_media_url:
        payload["media"] = {
            "url": qr_media_url,
            "filename": f"ticket-{ticket_code}.png",
        }

    await _post_with_retry(payload, phone=normalized_phone, ticket_code=ticket_code)


def _normalize_phone(phone: str) -> str:
    """Return digits-only phone with Indian country code prefix (91)."""
    digits = phone.strip().lstrip("+").replace(" ", "").replace("-", "")
    if len(digits) == 10:
        return f"91{digits}"
    return digits


async def _post_with_retry(payload: dict, *, phone: str, ticket_code: str) -> None:
    last_exc: Optional[Exception] = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(_AISENSY_API_URL, json=payload)

            if response.status_code == 200:
                logger.info(
                    "AiSensy WhatsApp sent | phone=%s | ticket=%s | attempt=%d",
                    phone,
                    ticket_code,
                    attempt,
                )
                return

            body_preview = response.text[:300]
            logger.warning(
                "AiSensy HTTP %d | phone=%s | ticket=%s | attempt=%d/%d | body=%s",
                response.status_code,
                phone,
                ticket_code,
                attempt,
                _MAX_RETRIES,
                body_preview,
            )
            last_exc = RuntimeError(
                f"AiSensy HTTP {response.status_code}: {body_preview}"
            )

            # 4xx = client error (bad API key, invalid campaign, etc.) — no point retrying
            if 400 <= response.status_code < 500:
                break

        except httpx.TimeoutException as exc:
            logger.warning(
                "AiSensy timeout | phone=%s | ticket=%s | attempt=%d/%d",
                phone,
                ticket_code,
                attempt,
                _MAX_RETRIES,
            )
            last_exc = exc
        except httpx.RequestError as exc:
            logger.warning(
                "AiSensy request error | phone=%s | ticket=%s | error=%s | attempt=%d/%d",
                phone,
                ticket_code,
                str(exc),
                attempt,
                _MAX_RETRIES,
            )
            last_exc = exc

        if attempt < _MAX_RETRIES:
            delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
            logger.info(
                "AiSensy retry in %.1fs | attempt %d → %d",
                delay,
                attempt,
                attempt + 1,
            )
            await asyncio.sleep(delay)

    raise RuntimeError(
        f"AiSensy failed after {_MAX_RETRIES} attempts for {phone}: {last_exc}"
    ) from last_exc
