"""Payments feature router — Razorpay verification, UPI UTR + screenshot submission, webhook."""

import asyncio
import hashlib
import hmac
import logging
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.domain.models.registration import Event, Payment, Registration
from src.features.registrations.schemas import PaymentVerifyRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments")

_SCREENSHOTS_DIR = Path("uploads") / "screenshots"
_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_SCREENSHOT_BYTES = 5 * 1024 * 1024  # 5 MB


# ── Mode guard ────────────────────────────────────────────────────────────────

def _require_mode(expected: str) -> None:
    """Raise 400 if the active payment mode is not ``expected``.

    All payment endpoints exist regardless of mode so that a future env-var
    switch never requires code changes. Calling an unsupported endpoint
    returns a clear error message instead of 404.
    """
    if settings.PAYMENT_MODE.upper() != expected:
        complement = "UPI_MANUAL" if expected == "RAZORPAY" else "RAZORPAY"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"This endpoint requires PAYMENT_MODE={expected}. "
                f"Current mode is {settings.PAYMENT_MODE.upper()}. "
                f"Switch to PAYMENT_MODE={complement} or use the correct endpoint."
            ),
        )


# ── Screenshot helper ─────────────────────────────────────────────────────────

async def _save_screenshot(file: UploadFile) -> str:
    """Validate, save, and return the relative URL path for a payment screenshot."""
    if file.content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Screenshot must be a JPEG, PNG, WEBP, or GIF image",
        )

    data = await file.read()
    if len(data) > _MAX_SCREENSHOT_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Screenshot must be under 5 MB",
        )

    ext = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }.get(file.content_type, ".jpg")

    _SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    (_SCREENSHOTS_DIR / filename).write_bytes(data)

    return f"/uploads/screenshots/{filename}"


# ── Admin notification helper ─────────────────────────────────────────────────

async def _notify_admin_new_payment(registration: Registration, payment: Payment) -> None:
    """Fire-and-forget: notify admin via WhatsApp (primary) and email (fallback)."""
    amount_rupees = str(payment.amount // 100)
    utr = payment.utr_reference or "—"
    dashboard_url = settings.ADMIN_DASHBOARD_URL

    if settings.ADMIN_WHATSAPP_NUMBER:
        try:
            from src.infrastructure.whatsapp_aisensy import send_admin_payment_notification
            await send_admin_payment_notification(
                admin_phone=settings.ADMIN_WHATSAPP_NUMBER,
                attendee_name=registration.name,
                attendee_phone=registration.phone,
                amount_rupees=amount_rupees,
                utr_reference=utr,
                dashboard_url=dashboard_url,
            )
            logger.info("Admin WhatsApp alert sent for UTR %s", utr)
        except Exception as exc:
            logger.warning("Admin WhatsApp alert failed for UTR %s: %s", utr, exc)

    if settings.ADMIN_EMAIL:
        try:
            from src.infrastructure.email import send_admin_payment_notification_email
            await send_admin_payment_notification_email(
                admin_email=settings.ADMIN_EMAIL,
                attendee_name=registration.name,
                attendee_phone=registration.phone,
                amount_rupees=amount_rupees,
                utr_reference=utr,
                dashboard_url=dashboard_url,
            )
            logger.info("Admin email alert sent for UTR %s", utr)
        except Exception as exc:
            logger.warning("Admin email alert failed for UTR %s: %s", utr, exc)


# ── RAZORPAY endpoints ────────────────────────────────────────────────────────

@router.post("/verify", summary="Verify Razorpay payment and generate ticket")
async def verify_payment(
    payload: PaymentVerifyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Available only when PAYMENT_MODE=RAZORPAY."""
    _require_mode("RAZORPAY")

    sign_string = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.get_secret_value().encode(),
        sign_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, payload.razorpay_signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature",
        )

    result = await db.execute(
        select(Payment).where(Payment.razorpay_order_id == payload.razorpay_order_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    payment.razorpay_payment_id = payload.razorpay_payment_id
    payment.razorpay_signature = payload.razorpay_signature
    payment.status = "success"

    result = await db.execute(
        select(Registration).where(Registration.id == payment.registration_id)
    )
    registration = result.scalar_one_or_none()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    registration.status = "confirmed"

    result = await db.execute(select(Event).where(Event.id == registration.event_id))
    event = result.scalar_one_or_none()

    await db.commit()

    from src.features.tickets.service import TicketService
    ticket_service = TicketService(db)
    ticket = await ticket_service.generate_and_deliver_ticket(registration)

    logger.info("Payment verified and ticket generated: %s", ticket.ticket_code)

    return {
        "status": "success",
        "ticket_code": ticket.ticket_code,
        "qr_code_url": ticket.qr_code_url,
        "attendee_name": registration.name,
        "email": registration.email,
        "quantity": registration.quantity,
        "event_name": event.name if event else "",
        "event_date": event.event_date.strftime("%A, %d %B %Y %I:%M %p IST") if event else "",
        "event_venue": event.venue if event else "",
    }


@router.post("/webhook", summary="Razorpay webhook handler")
async def razorpay_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Available only when PAYMENT_MODE=RAZORPAY."""
    _require_mode("RAZORPAY")

    x_razorpay_signature = request.headers.get("X-Razorpay-Signature", "")
    body = await request.body()
    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.get_secret_value().encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, x_razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event_data = await request.json()
    event_type = event_data.get("event")
    logger.info("Razorpay webhook received: %s", event_type)

    payment_payload = (
        event_data.get("payload", {}).get("payment", {}).get("entity")
        or event_data.get("payload", {}).get("order", {}).get("entity")
    )

    razorpay_order_id = payment_payload.get("order_id") if payment_payload else None
    if not razorpay_order_id:
        return {"status": "ignored", "event": event_type}

    result = await db.execute(
        select(Payment).where(Payment.razorpay_order_id == razorpay_order_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        logger.warning("Webhook payment record not found for order: %s", razorpay_order_id)
        return {"status": "not_found", "event": event_type}

    payment.status = "success"
    if payment_payload:
        payment.razorpay_payment_id = payment_payload.get("id") or payment.razorpay_payment_id
        payment.razorpay_signature = payment_payload.get("signature") or payment.razorpay_signature

    result = await db.execute(
        select(Registration).where(Registration.id == payment.registration_id)
    )
    registration = result.scalar_one_or_none()
    if registration:
        registration.status = "confirmed"
        from src.features.tickets.service import TicketService
        ticket_service = TicketService(db)
        await ticket_service.generate_and_deliver_ticket(registration)

    await db.commit()
    return {"status": "processed", "event": event_type}


# ── UPI_MANUAL endpoints ──────────────────────────────────────────────────────

@router.post("/submit-utr", summary="Submit UPI transaction ID and payment screenshot")
async def submit_utr(
    registration_id: Annotated[str, Form()],
    order_ref: Annotated[str, Form()],
    utr_reference: Annotated[str, Form(min_length=6, max_length=100)],
    screenshot: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Available only when PAYMENT_MODE=UPI_MANUAL.

    Saves the screenshot to disk and sets payment status to pending_verification.
    Admin then confirms via POST /admin/payments/{id}/confirm which issues the ticket.
    """
    _require_mode("UPI_MANUAL")

    screenshot_path = await _save_screenshot(screenshot)

    result = await db.execute(
        select(Payment).where(Payment.razorpay_order_id == order_ref)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Order reference not found")

    if payment.status not in ("initiated", "pending_verification"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Payment is already in status '{payment.status}'",
        )

    payment.utr_reference = utr_reference.strip()
    payment.payment_screenshot_url = screenshot_path
    payment.status = "pending_verification"
    await db.commit()

    logger.info("UTR submitted for order %s — UTR: %s", order_ref, utr_reference.strip())

    reg_result = await db.execute(
        select(Registration).where(Registration.id == payment.registration_id)
    )
    registration = reg_result.scalar_one_or_none()
    if registration:
        asyncio.create_task(_notify_admin_new_payment(registration, payment))

    return {
        "status": "pending_verification",
        "message": (
            "Your payment details have been submitted. "
            "Your ticket will be sent to your email and WhatsApp within 1–2 hours after verification."
        ),
        "registration_id": registration_id,
        "order_ref": order_ref,
    }
