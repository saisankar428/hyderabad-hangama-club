"""
Scanner feature router - QR ticket scanning at event entrance.
Used by event staff to validate attendee tickets.
"""

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
      description="Validates a ticket code and marks it as used. Returns attendee details.",
)
async def scan_ticket(
      payload: ScanRequest,
      db: Annotated[AsyncSession, Depends(get_db)],
) -> ScanResponse:
      """
          Scan a QR ticket at event entrance.

              - Returns attendee details if valid
                  - Marks ticket as USED after first scan
                      - Rejects already-used or cancelled tickets
                          """
      # Find ticket
      result = await db.execute(
          select(Ticket).where(Ticket.ticket_code == payload.ticket_code)
      )
      ticket = result.scalar_one_or_none()

    if not ticket:
              raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Ticket '{payload.ticket_code}' not found",
              )

    # Get registration details
    result = await db.execute(
              select(Registration).where(Registration.id == ticket.registration_id)
    )
    registration = result.scalar_one_or_none()

    if not registration:
              raise HTTPException(status_code=500, detail="Registration data corrupted")

    # Already scanned?
    if ticket.status == "used":
              logger.warning(f"Duplicate scan attempt: {payload.ticket_code}")
              return ScanResponse(
                  valid=False,
                  ticket_code=ticket.ticket_code,
                  attendee_name=registration.name,
                  event_id=str(registration.event_id),
                  message=f"Ticket already used at {ticket.scanned_at}",
                  already_scanned=True,
              )

    # Invalid statuses
    if ticket.status in ("expired", "cancelled"):
              return ScanResponse(
                            valid=False,
                            ticket_code=ticket.ticket_code,
                            attendee_name=registration.name,
                            event_id=str(registration.event_id),
                            message=f"Ticket is {ticket.status}",
              )

    # Mark as used
    ticket.status = "used"
    ticket.scanned_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info(f"Ticket scanned successfully: {payload.ticket_code} | {registration.name}")

    return ScanResponse(
              valid=True,
              ticket_code=ticket.ticket_code,
              attendee_name=registration.name,
              event_id=str(registration.event_id),
              message=f"Welcome, {registration.name}! Entry granted.",
    )
