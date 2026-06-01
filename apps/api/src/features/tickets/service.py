"""Ticket Service — QR generation, email and WhatsApp delivery."""

import base64
import io
import logging
from typing import Optional

import qrcode
from fpdf import FPDF
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.domain.models.registration import Event, Registration, Ticket
from src.infrastructure.email import send_ticket_email
from src.infrastructure.whatsapp_aisensy import send_ticket_whatsapp

logger = logging.getLogger(__name__)


def generate_ticket_code(next_number: int) -> str:
    return f"HHC-{next_number:06d}"


def generate_qr_code_base64(data: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def build_ticket_pdf(
    ticket_code: str,
    registration: Registration,
    event: Event,
    qr_base64: str,
) -> bytes:
    pdf = FPDF(format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(True, margin=15)
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 12, "Hyderabad Hangama Club", ln=True, align="C")
    pdf.ln(8)

    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, f"Ticket Code: {ticket_code}")
    pdf.multi_cell(0, 8, f"Attendee: {registration.name}")
    pdf.multi_cell(0, 8, f"Email: {registration.email}")
    pdf.multi_cell(0, 8, f"Phone: {registration.phone}")
    pdf.multi_cell(0, 8, f"Event: {event.name}")
    pdf.multi_cell(0, 8, f"Venue: {event.venue}")
    pdf.multi_cell(0, 8, f"Date: {event.event_date.strftime('%A, %d %B %Y %I:%M %p')}")
    pdf.multi_cell(0, 8, f"Tickets: {registration.quantity}")
    pdf.multi_cell(0, 8, "\nPresent this ticket at entry. Valid for one-time entry only.")

    return pdf.output(dest="S").encode("latin-1")


class TicketService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def _next_ticket_number(self) -> int:
        result = await self._db.execute(select(func.count()).select_from(Ticket))
        return int(result.scalar_one() or 0) + 1

    async def generate_and_deliver_ticket(self, registration: Registration) -> Ticket:
        if registration is None:
            raise ValueError("Registration is required to generate ticket")

        result = await self._db.execute(select(Event).where(Event.id == registration.event_id))
        event = result.scalar_one_or_none()
        if not event:
            raise ValueError("Event not found for ticket generation")

        ticket_code = generate_ticket_code(await self._next_ticket_number())
        qr_data = f"HHC:TICKET:{ticket_code}:{registration.id}"
        qr_base64 = generate_qr_code_base64(qr_data)

        ticket = Ticket(
            registration_id=registration.id,
            ticket_code=ticket_code,
            qr_code_url=f"data:image/png;base64,{qr_base64}",
            status="active",
        )
        self._db.add(ticket)
        await self._db.flush()

        try:
            pdf_bytes = build_ticket_pdf(ticket_code, registration, event, qr_base64)
            await send_ticket_email(
                to_email=registration.email,
                to_name=registration.name,
                ticket_code=ticket_code,
                qr_base64=qr_base64,
                ticket_pdf=pdf_bytes,
                event_name=event.name,
                event_date=event.event_date.strftime("%A, %d %B %Y %I:%M %p IST"),
                event_venue=event.venue,
                quantity=registration.quantity,
            )
            ticket.email_sent = True
            logger.info("Email sent for ticket: %s", ticket_code)
        except Exception as exc:
            logger.error("Email delivery failed for %s: %s", ticket_code, exc)

        try:
            whatsapp_phone = registration.whatsapp or registration.phone
            qr_media_url = (
                f"{settings.API_BASE_URL.rstrip('/')}/tickets/{ticket_code}/qr"
                if settings.API_BASE_URL
                else None
            )
            await send_ticket_whatsapp(
                phone=whatsapp_phone,
                name=registration.name,
                ticket_code=ticket_code,
                qr_media_url=qr_media_url,
            )
            ticket.whatsapp_sent = True
            logger.info("WhatsApp sent for ticket: %s", ticket_code)
        except Exception as exc:
            logger.error("WhatsApp delivery failed for %s: %s", ticket_code, exc)

        await self._db.commit()
        await self._db.refresh(ticket)
        return ticket

    async def get_ticket_by_code(self, ticket_code: str) -> Optional[Ticket]:
        result = await self._db.execute(select(Ticket).where(Ticket.ticket_code == ticket_code))
        return result.scalar_one_or_none()
