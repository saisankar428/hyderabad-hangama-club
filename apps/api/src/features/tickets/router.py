"""Tickets feature router - retrieve ticket details and QR codes."""

import uuid
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.domain.models.registration import Ticket

router = APIRouter(prefix="/tickets")


class TicketResponse(BaseModel):
      id: uuid.UUID
      registration_id: uuid.UUID
      ticket_code: str
      qr_code_url: Optional[str]
      status: str
      scanned_at: Optional[datetime]
      email_sent: bool
      whatsapp_sent: bool
      created_at: datetime

    model_config = {"from_attributes": True}


@router.get(
      "/{ticket_code}",
      response_model=TicketResponse,
      summary="Get ticket by code",
      description="Retrieve ticket details including QR code by ticket code.",
)
async def get_ticket(
      ticket_code: str,
      db: Annotated[AsyncSession, Depends(get_db)],
) -> TicketResponse:
      result = await db.execute(
                select(Ticket).where(Ticket.ticket_code == ticket_code)
      )
      ticket = result.scalar_one_or_none()
      if not ticket:
                raise HTTPException(status_code=404, detail=f"Ticket '{ticket_code}' not found")
            return TicketResponse.model_validate(ticket)
