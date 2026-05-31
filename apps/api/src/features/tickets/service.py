"""
Ticket Service - QR generation, Email + WhatsApp delivery.
Core feature of the Hyderabad Hangama Club ticketing flow.
"""

import base64
import io
import logging
import secrets
import string
from typing import Optional

import qrcode
from qrcode.image.pure import PyPNGImage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.domain.models.registration import Registration, Ticket
from src.infrastructure.email import send_ticket_email
from src.infrastructure.whatsapp import send_ticket_whatsapp

logger = logging.getLogger(__name__)

TICKET_CODE_LENGTH = 12
TICKET_CODE_ALPHABET = string.ascii_uppercase + string.digits


def generate_ticket_code() -> str:
      """Generate a unique, human-readable ticket code (e.g. HHC-A3X9K2P7M1Q5)."""
      random_part = "".join(secrets.choice(TICKET_CODE_ALPHABET) for _ in range(TICKET_CODE_LENGTH))
      return f"HHC-{random_part}"


def generate_qr_code_base64(data: str) -> str:
      """Generate QR code as base64-encoded PNG string."""
      qr = qrcode.QRCode(
          version=1,
          error_correction=qrcode.constants.ERROR_CORRECT_H,
          box_size=10,
          border=4,
      )
      qr.add_data(data)
      qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


class TicketService:
      """Handles ticket generation and multi-channel delivery."""

    def __init__(self, db: AsyncSession) -> None:
              self._db = db

    async def generate_and_deliver_ticket(self, registration: Registration) -> Ticket:
              """
                      Generate QR ticket and deliver via Email + WhatsApp.

                              Returns the created Ticket model.
                                      """
              ticket_code = generate_ticket_code()
              qr_data = f"HHC:TICKET:{ticket_code}:{registration.id}"
              qr_base64 = generate_qr_code_base64(qr_data)

        # Persist ticket
              ticket = Ticket(
                  registration_id=registration.id,
                  ticket_code=ticket_code,
                  qr_code_url=f"data:image/png;base64,{qr_base64}",
                  status="active",
              )
              self._db.add(ticket)
              await self._db.flush()

        # Deliver via email (non-blocking on failure)
              try:
                            await send_ticket_email(
                                              to_email=registration.email,
                                              to_name=registration.name,
                                              ticket_code=ticket_code,
                                              qr_base64=qr_base64,
                            )
                            ticket.email_sent = True
                            logger.info(f"Email sent for ticket: {ticket_code}")
except Exception as e:
            logger.error(f"Email delivery failed for {ticket_code}: {e}")

        # Deliver via WhatsApp (non-blocking on failure)
        try:
                      await send_ticket_whatsapp(
                                        phone=registration.phone,
                                        name=registration.name,
                                        ticket_code=ticket_code,
                      )
                      ticket.whatsapp_sent = True
                      logger.info(f"WhatsApp sent for ticket: {ticket_code}")
except Exception as e:
              logger.error(f"WhatsApp delivery failed for {ticket_code}: {e}")

        await self._db.commit()
        await self._db.refresh(ticket)
        return ticket

    async def get_ticket_by_code(self, ticket_code: str) -> Optional[Ticket]:
              """Fetch a ticket by its unique code."""
              result = await self._db.execute(
                  select(Ticket).where(Ticket.ticket_code == ticket_code)
              )
              return result.scalar_one_or_none()
