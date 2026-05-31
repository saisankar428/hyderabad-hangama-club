"""
Email infrastructure - SendGrid integration for ticket delivery.
Infrastructure layer: external service adapter.
"""

import asyncio
import logging
from functools import partial

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Attachment,
    Disposition,
    FileContent,
    FileName,
    FileType,
    Mail,
)

from src.core.config import settings

logger = logging.getLogger(__name__)

EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
    <title>Your Hyderabad Hangama Club Ticket</title>
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center;">
          <h1 style="color: white; margin: 0;">Hyderabad Hangama Club</h1>
              <p style="color: rgba(255,255,255,0.9);">Your ticket is confirmed!</p>
                </div>
                  <div style="padding: 30px; background: #f9f9f9; border-radius: 0 0 10px 10px;">
                      <h2>Hello, {name}!</h2>
                          <p>Your registration is confirmed. Here is your ticket:</p>
                              <div style="background: white; border: 2px dashed #667eea; padding: 20px; border-radius: 8px; text-align: center;">
                                    <p style="font-size: 24px; font-weight: bold; color: #667eea; letter-spacing: 2px;">{ticket_code}</p>
                                          <p style="color: #666;">Show this QR code at the entrance</p>
                                                <img src="cid:qrcode" alt="QR Code" style="width: 200px; height: 200px;" />
                                                    </div>
                                                        <p style="color: #999; font-size: 12px; margin-top: 20px;">
                                                              This ticket is valid for one-time entry only. Do not share it.
                                                                  </p>
                                                                    </div>
                                                                    </body>
                                                                    </html>
                                                                    """


async def send_ticket_email(
      to_email: str,
      to_name: str,
      ticket_code: str,
      qr_base64: str,
) -> None:
      """Send ticket email with QR code attachment via SendGrid."""

    html_content = EMAIL_TEMPLATE.format(name=to_name, ticket_code=ticket_code)

    message = Mail(
              from_email=(settings.EMAIL_FROM, settings.EMAIL_FROM_NAME),
              to_emails=to_email,
              subject=f"Your Ticket: {ticket_code} - Hyderabad Hangama Club",
              html_content=html_content,
    )

    # Attach QR code inline
    attachment = Attachment(
              FileContent(qr_base64),
              FileName("ticket_qr.png"),
              FileType("image/png"),
              Disposition("inline"),
    )
    attachment.content_id = "qrcode"
    message.attachment = attachment

    # Run sync SDK in thread pool
    loop = asyncio.get_event_loop()
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    send_fn = partial(sg.send, message)
    response = await loop.run_in_executor(None, send_fn)

    if response.status_code not in (200, 202):
              raise RuntimeError(f"SendGrid error: {response.status_code} - {response.body}")

    logger.info(f"Email sent to {to_email} | Ticket: {ticket_code}")
