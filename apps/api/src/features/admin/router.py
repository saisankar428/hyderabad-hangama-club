import uuid
from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.domain.models.registration import Payment, Registration, Ticket

router = APIRouter(prefix="/admin")


def verify_admin_key(x_admin_key: str = Header(..., alias="X-ADMIN-KEY")) -> None:
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin API key")


class AdminMetricsResponse(BaseModel):
    total_registrations: int
    total_revenue: int
    total_checked_in: int


class AdminTicketResponse(BaseModel):
    ticket_code: str
    status: str
    scanned_at: Optional[datetime]
    registration_id: uuid.UUID
    attendee_name: str
    email: str
    phone: str
    registration_status: str
    payment_status: str
    amount: int
    currency: str


class PendingPaymentResponse(BaseModel):
    id: uuid.UUID
    registration_id: uuid.UUID
    order_ref: Optional[str]
    amount: int
    currency: str
    utr_reference: Optional[str]
    payment_screenshot_url: Optional[str]
    attendee_name: str
    email: str
    phone: str
    quantity: int
    created_at: datetime


@router.get("/metrics", response_model=AdminMetricsResponse, summary="Get admin metrics")
async def get_metrics(
    _: Annotated[None, Depends(verify_admin_key)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AdminMetricsResponse:
    total_registrations = await db.scalar(select(func.count()).select_from(Registration))

    total_revenue = await db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == "success")
    )

    total_checked_in = await db.scalar(
        select(func.count()).select_from(Ticket).where(Ticket.status == "used")
    )

    return AdminMetricsResponse(
        total_registrations=int(total_registrations or 0),
        total_revenue=int(total_revenue or 0),
        total_checked_in=int(total_checked_in or 0),
    )


@router.get("/tickets/search", response_model=AdminTicketResponse, summary="Search ticket by code")
async def search_ticket(
    _: Annotated[None, Depends(verify_admin_key)],
    db: Annotated[AsyncSession, Depends(get_db)],
    ticket_code: str = Query(..., description="Ticket code to search"),
) -> AdminTicketResponse:
    result = await db.execute(select(Ticket, Registration, Payment).join(Registration, Ticket.registration_id == Registration.id).join(Payment, Payment.registration_id == Registration.id).where(Ticket.ticket_code == ticket_code))
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    ticket, registration, payment = row
    return AdminTicketResponse(
        ticket_code=ticket.ticket_code,
        status=ticket.status,
        scanned_at=ticket.scanned_at,
        registration_id=ticket.registration_id,
        attendee_name=registration.name,
        email=registration.email,
        phone=registration.phone,
        registration_status=registration.status,
        payment_status=payment.status,
        amount=payment.amount,
        currency=payment.currency,
    )


@router.get("/payments/pending", response_model=List[PendingPaymentResponse], summary="List UPI payments awaiting verification")
async def list_pending_payments(
    _: Annotated[None, Depends(verify_admin_key)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> List[PendingPaymentResponse]:
    result = await db.execute(
        select(Payment, Registration)
        .join(Registration, Payment.registration_id == Registration.id)
        .where(Payment.status == "pending_verification")
        .order_by(Payment.created_at.asc())
    )
    rows = result.all()

    return [
        PendingPaymentResponse(
            id=payment.id,
            registration_id=payment.registration_id,
            order_ref=payment.razorpay_order_id,
            amount=payment.amount,
            currency=payment.currency,
            utr_reference=payment.utr_reference,
            payment_screenshot_url=payment.payment_screenshot_url,
            attendee_name=registration.name,
            email=registration.email,
            phone=registration.phone,
            quantity=registration.quantity,
            created_at=payment.created_at,
        )
        for payment, registration in rows
    ]


@router.post("/payments/{payment_id}/reject", summary="Reject UPI payment proof")
async def reject_payment(
    payment_id: uuid.UUID,
    _: Annotated[None, Depends(verify_admin_key)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status not in ("pending_verification", "initiated"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Payment cannot be rejected from status '{payment.status}'",
        )

    payment.status = "failed"

    result = await db.execute(select(Registration).where(Registration.id == payment.registration_id))
    registration = result.scalar_one_or_none()
    if registration:
        registration.status = "payment_pending"

    await db.commit()

    return {"status": "rejected", "payment_id": str(payment_id)}


@router.post("/payments/{payment_id}/confirm", summary="Confirm UPI payment and generate ticket")
async def confirm_payment(
    payment_id: uuid.UUID,
    _: Annotated[None, Depends(verify_admin_key)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    result = await db.execute(select(Registration).where(Registration.id == payment.registration_id))
    registration = result.scalar_one_or_none()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    # Idempotency: if a ticket already exists for this registration, return it directly
    existing_ticket = await db.scalar(select(Ticket).where(Ticket.registration_id == registration.id))
    if existing_ticket:
        return {
            "status": "already_confirmed",
            "ticket_code": existing_ticket.ticket_code,
            "attendee_name": registration.name,
            "email": registration.email,
        }

    if payment.status == "success":
        raise HTTPException(status_code=409, detail="Payment already confirmed but no ticket found — contact support")

    payment.status = "success"
    registration.status = "confirmed"
    await db.commit()

    from src.features.tickets.service import TicketService
    ticket_service = TicketService(db)
    ticket = await ticket_service.generate_and_deliver_ticket(registration)

    return {
        "status": "confirmed",
        "ticket_code": ticket.ticket_code,
        "attendee_name": registration.name,
        "email": registration.email,
    }
