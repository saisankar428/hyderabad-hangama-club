"""
Email infrastructure - Resend integration for ticket delivery.
Infrastructure layer: external service adapter.
"""

import asyncio
import base64
import logging
from functools import partial
from typing import Optional

import resend

from src.core.config import settings

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_BASE_DELAY_SECONDS = 1.0

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Your Hyderabad Hangama Club Ticket</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f4f8;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#f4f4f8;">
    <tr>
      <td align="center" style="padding:40px 16px;">

        <!-- Card -->
        <table width="600" cellpadding="0" cellspacing="0" role="presentation"
               style="max-width:600px;width:100%;background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#7c3aed 0%,#4f46e5 100%);padding:40px 32px;text-align:center;">
              <p style="margin:0 0 8px 0;font-size:13px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:rgba(255,255,255,0.75);">
                HYDERABAD HANGAMA CLUB
              </p>
              <h1 style="margin:0;font-size:28px;font-weight:700;color:#ffffff;line-height:1.2;">
                You&rsquo;re In! 🎉
              </h1>
              <p style="margin:12px 0 0 0;font-size:15px;color:rgba(255,255,255,0.85);">
                Your ticket is confirmed and ready.
              </p>
            </td>
          </tr>

          <!-- Greeting -->
          <tr>
            <td style="padding:32px 40px 0 40px;">
              <p style="margin:0;font-size:18px;font-weight:600;color:#1e1b4b;">
                Hello, {name}!
              </p>
              <p style="margin:8px 0 0 0;font-size:15px;color:#6b7280;line-height:1.6;">
                We&rsquo;re thrilled to have you join us. Find your ticket details below &mdash;
                your PDF ticket is also attached to this email.
              </p>
            </td>
          </tr>

          <!-- Ticket code card -->
          <tr>
            <td style="padding:24px 40px 0 40px;">
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation"
                     style="background:linear-gradient(135deg,#f5f3ff 0%,#ede9fe 100%);border:2px dashed #7c3aed;border-radius:10px;">
                <tr>
                  <td style="padding:24px;text-align:center;">
                    <p style="margin:0 0 4px 0;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#7c3aed;">
                      TICKET CODE
                    </p>
                    <p style="margin:0;font-size:30px;font-weight:800;letter-spacing:4px;color:#4f46e5;">
                      {ticket_code}
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Event details -->
          <tr>
            <td style="padding:24px 40px 0 40px;">
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation"
                     style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;">
                <tr>
                  <td style="background:#f9fafb;padding:16px 20px;border-bottom:1px solid #e5e7eb;">
                    <p style="margin:0;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#9ca3af;">EVENT</p>
                    <p style="margin:4px 0 0 0;font-size:15px;font-weight:600;color:#111827;">{event_name}</p>
                  </td>
                </tr>
                <tr>
                  <td style="background:#ffffff;padding:16px 20px;border-bottom:1px solid #e5e7eb;">
                    <p style="margin:0;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#9ca3af;">DATE &amp; TIME</p>
                    <p style="margin:4px 0 0 0;font-size:15px;font-weight:600;color:#111827;">{event_date}</p>
                  </td>
                </tr>
                <tr>
                  <td style="background:#f9fafb;padding:16px 20px;border-bottom:1px solid #e5e7eb;">
                    <p style="margin:0;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#9ca3af;">VENUE</p>
                    <p style="margin:4px 0 0 0;font-size:15px;font-weight:600;color:#111827;">{event_venue}</p>
                  </td>
                </tr>
                <tr>
                  <td style="background:#f9fafb;padding:16px 20px;border-bottom:1px solid #e5e7eb;">
                    <p style="margin:0;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#9ca3af;">TICKETS</p>
                    <p style="margin:4px 0 0 0;font-size:15px;font-weight:600;color:#111827;">{quantity}</p>
                  </td>
                </tr>
                <tr>
                  <td style="background:#ffffff;padding:16px 20px;">
                    <p style="margin:0;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#9ca3af;">MOBILE</p>
                    <p style="margin:4px 0 0 0;font-size:15px;font-weight:600;color:#111827;">{phone}</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- QR Code -->
          <tr>
            <td style="padding:24px 40px 0 40px;text-align:center;">
              <p style="margin:0 0 16px 0;font-size:14px;color:#6b7280;">
                Show this QR code at the entrance
              </p>
              <img src="{qr_data_uri}" alt="Ticket QR Code"
                   width="200" height="200"
                   style="display:block;margin:0 auto;border:8px solid #f3f4f6;border-radius:12px;" />
            </td>
          </tr>

          <!-- Notice -->
          <tr>
            <td style="padding:24px 40px 0 40px;">
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation"
                     style="background:#fef3c7;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;">
                <tr>
                  <td style="padding:14px 16px;">
                    <p style="margin:0;font-size:13px;color:#92400e;line-height:1.5;">
                      <strong>Important:</strong> This ticket is valid for <strong>{quantity}</strong> attendee(s)
                      and can only be scanned once. Please do not share this ticket.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:32px 40px;text-align:center;border-top:1px solid #f3f4f6;margin-top:24px;">
              <p style="margin:0;font-size:13px;color:#9ca3af;line-height:1.6;">
                Questions? Reply to this email or reach out to us.<br />
                &copy; 2026 Hyderabad Hangama Club. All rights reserved.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


async def _send_with_retry(send_fn, ticket_code: str) -> None:
    last_exc: Optional[Exception] = None
    for attempt in range(_MAX_RETRIES):
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, send_fn)
            return
        except Exception as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES - 1:
                delay = _BASE_DELAY_SECONDS * (2 ** attempt)
                logger.warning(
                    f"Email send attempt {attempt + 1}/{_MAX_RETRIES} failed for {ticket_code}, "
                    f"retrying in {delay:.0f}s: {exc}"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"All {_MAX_RETRIES} email send attempts failed for {ticket_code}: {exc}"
                )
    raise last_exc  # type: ignore[misc]


_ADMIN_ALERT_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>New Payment Submitted</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f8;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f8;">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="560" cellpadding="0" cellspacing="0"
             style="max-width:560px;width:100%;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#d97706 0%,#7c3aed 100%);padding:32px;text-align:center;">
            <p style="margin:0 0 6px;font-size:11px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:rgba(255,255,255,0.75);">
              HYDERABAD HANGAMA CLUB — ADMIN ALERT
            </p>
            <h1 style="margin:0;font-size:22px;font-weight:800;color:#fff;">
              New Payment Submitted
            </h1>
          </td>
        </tr>
        <!-- Details -->
        <tr>
          <td style="padding:32px 40px;">
            <p style="margin:0 0 20px;font-size:15px;color:#374151;">
              A customer has submitted payment proof. Please review and approve or reject from the admin dashboard.
            </p>
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;">
              <tr style="background:#f9fafb;">
                <td style="padding:12px 16px;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#9ca3af;border-bottom:1px solid #e5e7eb;width:40%;">Name</td>
                <td style="padding:12px 16px;font-size:15px;font-weight:600;color:#111827;border-bottom:1px solid #e5e7eb;">{attendee_name}</td>
              </tr>
              <tr>
                <td style="padding:12px 16px;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#9ca3af;border-bottom:1px solid #e5e7eb;">Mobile</td>
                <td style="padding:12px 16px;font-size:15px;font-weight:600;color:#111827;border-bottom:1px solid #e5e7eb;">{attendee_phone}</td>
              </tr>
              <tr style="background:#f9fafb;">
                <td style="padding:12px 16px;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#9ca3af;border-bottom:1px solid #e5e7eb;">Amount</td>
                <td style="padding:12px 16px;font-size:15px;font-weight:700;color:#d97706;border-bottom:1px solid #e5e7eb;">&#8377;{amount_rupees}</td>
              </tr>
              <tr>
                <td style="padding:12px 16px;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#9ca3af;">Transaction ID</td>
                <td style="padding:12px 16px;font-size:14px;font-family:monospace;font-weight:700;color:#4f46e5;">{utr_reference}</td>
              </tr>
            </table>
            {dashboard_section}
          </td>
        </tr>
        <tr>
          <td style="padding:20px 40px 32px;text-align:center;border-top:1px solid #f3f4f6;">
            <p style="margin:0;font-size:12px;color:#9ca3af;">
              &copy; 2026 Hyderabad Hangama Club. This is an automated admin notification.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""

_DASHBOARD_BUTTON = """\
<div style="margin-top:24px;text-align:center;">
  <a href="{url}" style="display:inline-block;padding:14px 32px;background:linear-gradient(135deg,#d97706,#7c3aed);color:#fff;font-weight:700;font-size:14px;letter-spacing:0.08em;text-transform:uppercase;border-radius:8px;text-decoration:none;">
    View Admin Dashboard
  </a>
</div>
"""


async def send_admin_payment_notification_email(
    admin_email: str,
    attendee_name: str,
    attendee_phone: str,
    amount_rupees: str,
    utr_reference: str,
    dashboard_url: str = "",
) -> None:
    """Send an email alert to the admin when a customer submits payment proof."""
    resend.api_key = settings.RESEND_API_KEY

    dashboard_section = _DASHBOARD_BUTTON.format(url=dashboard_url) if dashboard_url else ""

    html_body = _ADMIN_ALERT_TEMPLATE.format(
        attendee_name=attendee_name,
        attendee_phone=attendee_phone,
        amount_rupees=amount_rupees,
        utr_reference=utr_reference,
        dashboard_section=dashboard_section,
    )

    params: resend.Emails.SendParams = {
        "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
        "to": [admin_email],
        "subject": f"[Action Required] New Payment: {attendee_name} — ₹{amount_rupees}",
        "html": html_body,
    }

    send_fn = partial(resend.Emails.send, params)
    await _send_with_retry(send_fn, f"admin-alert-{utr_reference}")

    logger.info("Admin alert email sent to %s for UTR %s", admin_email, utr_reference)


async def send_ticket_email(
    to_email: str,
    to_name: str,
    ticket_code: str,
    qr_base64: str,
    ticket_pdf: bytes,
    event_name: str = "",
    event_date: str = "",
    event_venue: str = "",
    quantity: int = 1,
    phone: str = "",
) -> None:
    resend.api_key = settings.RESEND_API_KEY

    qr_data_uri = f"data:image/png;base64,{qr_base64}"

    html_body = _HTML_TEMPLATE.format(
        name=to_name,
        ticket_code=ticket_code,
        event_name=event_name or "Hyderabad Hangama Club Event",
        event_date=event_date or "See your ticket PDF for details",
        event_venue=event_venue or "See your ticket PDF for details",
        quantity=quantity,
        phone=phone or "—",
        qr_data_uri=qr_data_uri,
    )

    pdf_b64 = base64.b64encode(ticket_pdf).decode("utf-8")

    params: resend.Emails.SendParams = {
        "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
        "to": [to_email],
        "subject": f"Your Ticket: {ticket_code} — Hyderabad Hangama Club",
        "html": html_body,
        "attachments": [
            {
                "filename": f"ticket_{ticket_code}.pdf",
                "content": pdf_b64,
                "content_type": "application/pdf",
            },
        ],
    }

    send_fn = partial(resend.Emails.send, params)
    await _send_with_retry(send_fn, ticket_code)

    logger.info(f"Email sent to {to_email} | Ticket: {ticket_code}")
