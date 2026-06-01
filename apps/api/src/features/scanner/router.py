"""Scanner feature router — QR ticket scanning at event entrance."""

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.domain.models.registration import Registration, Ticket

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scanner")


class ScanRequest(BaseModel):
    ticket_code: str


class ScanResponse(BaseModel):
    valid: bool
    ticket_code: str
    attendee_name: str
    event_id: str
    message: str
    already_scanned: bool = False


@router.post(
    "/scan",
    response_model=ScanResponse,
    summary="Scan QR ticket at event entrance",
)
async def scan_ticket(
    payload: ScanRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ScanResponse:
    result = await db.execute(select(Ticket).where(Ticket.ticket_code == payload.ticket_code))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{payload.ticket_code}' not found",
        )

    result = await db.execute(select(Registration).where(Registration.id == ticket.registration_id))
    registration = result.scalar_one_or_none()
    if not registration:
        raise HTTPException(status_code=500, detail="Registration data corrupted")

    if ticket.status == "used":
        logger.warning("Duplicate scan attempt: %s", payload.ticket_code)
        return ScanResponse(
            valid=False,
            ticket_code=ticket.ticket_code,
            attendee_name=registration.name,
            event_id=str(registration.event_id),
            message=f"Ticket already used at {ticket.scanned_at}",
            already_scanned=True,
        )

    if ticket.status in ("expired", "cancelled"):
        return ScanResponse(
            valid=False,
            ticket_code=ticket.ticket_code,
            attendee_name=registration.name,
            event_id=str(registration.event_id),
            message=f"Ticket is {ticket.status}",
        )

    ticket.status = "used"
    ticket.scanned_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info("Ticket scanned: %s | %s", payload.ticket_code, registration.name)

    return ScanResponse(
        valid=True,
        ticket_code=ticket.ticket_code,
        attendee_name=registration.name,
        event_id=str(registration.event_id),
        message=f"Welcome, {registration.name}! Entry granted.",
    )


@router.post("/checkin", response_model=ScanResponse, summary="Check in a ticket")
async def checkin_ticket(
    payload: ScanRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ScanResponse:
    return await scan_ticket(payload, db)
