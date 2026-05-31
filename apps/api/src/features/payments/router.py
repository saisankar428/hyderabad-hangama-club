"""
Payments feature router.
Handles Razorpay payment verification and webhook processing.
"""

import hashlib
import hmac
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.domain.models.registration import Payment, Registration, Ticket
from src.features.registrations.schemas import PaymentVerifyRequest
from src.features.tickets.service import TicketService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments")


@router.post("/verify", summary="Verify Razorpay payment and generate ticket")
async def verify_payment(
      payload: PaymentVerifyRequest,
      db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
      """
          Verify Razorpay payment signature.
              On success: confirm registration, generate QR ticket, send email + WhatsApp.
                  """
      # Verify signature
      sign_string = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
      expected_signature = hmac.new(
          settings.RAZORPAY_KEY_SECRET.encode(),
          sign_string.encode(),
          hashlib.sha256,
      ).hexdigest()

    if not hmac.compare_digest(expected_signature, payload.razorpay_signature):
              raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid payment signature",
              )

    # Update payment record
    result = await db.execute(
              select(Payment).where(Payment.razorpay_order_id == payload.razorpay_order_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
              raise HTTPException(status_code=404, detail="Payment record not found")

    payment.razorpay_payment_id = payload.razorpay_payment_id
    payment.razorpay_signature = payload.razorpay_signature
    payment.status = "success"

    # Update registration status
    result = await db.execute(
              select(Registration).where(Registration.id == payment.registration_id)
    )
    registration = result.scalar_one_or_none()
    if registration:
              registration.status = "confirmed"

    await db.commit()

    # Generate ticket and send notifications
    ticket_service = TicketService(db)
    ticket = await ticket_service.generate_and_deliver_ticket(registration)

    logger.info(f"Payment verified and ticket generated: {ticket.ticket_code}")
    return {"status": "success", "ticket_code": ticket.ticket_code}


@router.post("/webhook", summary="Razorpay webhook handler")
async def razorpay_webhook(
      request: Request,
      x_razorpay_signature: Annotated[str, Header()],
      db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
      """Handle Razorpay webhooks for payment status updates."""
      body = await request.body()

    # Verify webhook signature
      expected = hmac.new(
          settings.RAZORPAY_WEBHOOK_SECRET.encode(),
          body,
          hashlib.sha256,
      ).hexdigest()

    if not hmac.compare_digest(expected, x_razorpay_signature):
              raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event_data = await request.json()
    event_type = event_data.get("event")

    logger.info(f"Razorpay webhook received: {event_type}")
    return {"status": "received"}
