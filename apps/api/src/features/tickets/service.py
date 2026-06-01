"""Ticket Service — QR generation, PDF building, email and WhatsApp delivery."""

import base64
import io
import logging
import os
import tempfile
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


def _s(text: str) -> str:
    """Encode to Latin-1 safe string for fpdf 1.7.x (replace unencodable chars)."""
    return str(text).encode("latin-1", "replace").decode("latin-1")


def build_ticket_pdf(
    ticket_code: str,
    registration: Registration,
    event: Event,
    qr_base64: str,
) -> bytes:
    """Build an A4 PDF ticket with QR code embedded.

    Layout:
      Header (club name + "EVENT TICKET")
      Ticket code box
      Attendee section: Name, Mobile, Email, Tickets
      Event section: Event, Venue, Date, Time
      QR code (centered, 60mm)
      Footer notice
    """
    pdf = FPDF("P", "mm", "A4")
    pdf.add_page()
    pdf.set_auto_page_break(True, margin=15)

    LM = 15   # left margin
    RM = 195  # right margin (210 - 15)
    LW = 45   # label column width

    # ── Header ─────────────────────────────────────────────────────
    pdf.set_fill_color(30, 10, 80)
    pdf.rect(0, 0, 210, 36, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 19)
    pdf.set_xy(0, 9)
    pdf.cell(210, 10, _s("HYDERABAD HANGAMA CLUB"), ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(212, 175, 55)
    pdf.cell(210, 7, _s("EVENT TICKET"), ln=True, align="C")

    # Ensure next content starts below the 36mm header rect with 8mm gap
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(44)

    # ── Ticket code box ─────────────────────────────────────────────
    box_y = pdf.get_y()
    pdf.set_fill_color(245, 240, 255)
    pdf.set_draw_color(124, 58, 237)
    pdf.rect(LM, box_y, 180, 20, "FD")

    pdf.set_font("Arial", "B", 7)
    pdf.set_text_color(124, 58, 237)
    pdf.set_xy(LM, box_y + 3)
    pdf.cell(180, 5, _s("TICKET CODE"), ln=True, align="C")

    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(30, 10, 80)
    pdf.set_x(LM)
    pdf.cell(180, 10, _s(ticket_code), ln=True, align="C")

    pdf.set_draw_color(0, 0, 0)
    pdf.set_fill_color(255, 255, 255)
    pdf.ln(8)

    # ── Section helper ───────────────────────────────────────────────
    def section_header(title: str) -> None:
        pdf.set_font("Arial", "B", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, _s(title), ln=True)
        pdf.set_draw_color(212, 175, 55)
        pdf.line(LM, pdf.get_y(), RM, pdf.get_y())
        pdf.set_draw_color(0, 0, 0)
        pdf.ln(3)

    def row(label: str, value: str) -> None:
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(90, 90, 90)
        pdf.cell(LW, 7, _s(label + ":"), ln=False)
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(0, 0, 0)
        # Use multi_cell for value to handle wrapping, but keep x alignment
        pdf.multi_cell(0, 7, _s(value))

    # ── Attendee ────────────────────────────────────────────────────
    section_header("ATTENDEE DETAILS")
    row("Name", registration.name)
    row("Mobile", registration.phone)
    row("Email", registration.email)
    row("Tickets", str(registration.quantity))
    pdf.ln(5)

    # ── Event ────────────────────────────────────────────────────────
    section_header("EVENT DETAILS")
    row("Event", event.name)
    row("Venue", event.venue)
    row("Date", event.event_date.strftime("%A, %d %B %Y"))
    row("Time", event.event_date.strftime("%I:%M %p IST"))
    pdf.ln(5)

    # ── QR Code ──────────────────────────────────────────────────────
    section_header("PRESENT AT ENTRY — SCAN ONCE")
    pdf.ln(2)

    qr_size = 60  # mm
    qr_x = (210 - qr_size) / 2

    # Write QR bytes to a temp file (fpdf 1.7.x requires a file path)
    fd, tmp_path = tempfile.mkstemp(suffix=".png")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(base64.b64decode(qr_base64))
        pdf.image(tmp_path, x=qr_x, y=None, w=qr_size)
    except Exception as exc:
        logger.warning("QR image could not be embedded in PDF: %s", exc)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    pdf.ln(4)

    # ── Footer ───────────────────────────────────────────────────────
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(160, 160, 160)
    pdf.cell(0, 5, _s("Valid for one-time entry only. Do not share this ticket."), ln=True, align="C")

    # ── Output bytes (fpdf 1.7.x returns str; fpdf2 returns bytes) ──
    raw = pdf.output(dest="S")
    return raw if isinstance(raw, bytes) else raw.encode("latin-1")


class TicketService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def _next_ticket_number(self) -> int:
        result = await self._db.execute(select(func.count()).select_from(Ticket))
        return int(result.scalar_one() or 0) + 1

    async def generate_and_deliver_ticket(self, registration: Registration) -> Ticket:
        if registration is None:
            raise ValueError("Registration is required to generate ticket")

        # Idempotency: return existing ticket if one was already issued for this registration
        existing = await self._db.execute(
            select(Ticket).where(Ticket.registration_id == registration.id)
        )
        existing_ticket = existing.scalar_one_or_none()
        if existing_ticket:
            logger.info(
                "Ticket already exists for registration %s: %s — skipping duplicate generation",
                registration.id,
                existing_ticket.ticket_code,
            )
            return existing_ticket

        result = await self._db.execute(select(Event).where(Event.id == registration.event_id))
        event = result.scalar_one_or_none()
        if not event:
            raise ValueError("Event not found for ticket generation")

        # ── 1. Generate ticket code + QR ──────────────────────────────
        ticket_code = generate_ticket_code(await self._next_ticket_number())
        qr_data = f"HHC:TICKET:{ticket_code}:{registration.id}"
        qr_base64 = generate_qr_code_base64(qr_data)

        # ── 2. Persist ticket record ──────────────────────────────────
        ticket = Ticket(
            registration_id=registration.id,
            ticket_code=ticket_code,
            qr_code_url=f"data:image/png;base64,{qr_base64}",
            status="active",
        )
        self._db.add(ticket)
        await self._db.flush()

        # Formatted strings shared across channels
        event_date_str = event.event_date.strftime("%A, %d %B %Y")
        event_time_str = event.event_date.strftime("%I:%M %p IST")
        event_datetime_str = f"{event_date_str} at {event_time_str}"

        # ── 3. Build PDF ──────────────────────────────────────────────
        pdf_bytes = build_ticket_pdf(ticket_code, registration, event, qr_base64)

        # ── 4. Send email (PDF + QR embedded in HTML body) ────────────
        try:
            await send_ticket_email(
                to_email=registration.email,
                to_name=registration.name,
                phone=registration.phone,
                ticket_code=ticket_code,
                qr_base64=qr_base64,
                ticket_pdf=pdf_bytes,
                event_name=event.name,
                event_date=event_datetime_str,
                event_venue=event.venue,
                quantity=registration.quantity,
            )
            ticket.email_sent = True
            logger.info("Email sent for ticket %s", ticket_code)
        except Exception as exc:
            logger.error("Email delivery failed for %s: %s", ticket_code, exc)

        # ── 5. Send WhatsApp (QR image + confirmation message) ────────
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
                event_name=event.name,
                event_date=event_date_str,
                event_time=event_time_str,
                event_venue=event.venue,
            )
            ticket.whatsapp_sent = True
            logger.info("WhatsApp sent for ticket %s", ticket_code)
        except Exception as exc:
            logger.error("WhatsApp delivery failed for %s: %s", ticket_code, exc)

        # ── 6. Commit ─────────────────────────────────────────────────
        await self._db.commit()
        await self._db.refresh(ticket)
        return ticket

    async def get_ticket_by_code(self, ticket_code: str) -> Optional[Ticket]:
        result = await self._db.execute(select(Ticket).where(Ticket.ticket_code == ticket_code))
        return result.scalar_one_or_none()
