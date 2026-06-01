import uuid
from datetime import datetime
from typing import Annotated, Optional

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
