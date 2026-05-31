"""
WhatsApp infrastructure - Twilio integration for ticket delivery.
Infrastructure layer: external service adapter.
"""

import asyncio
import logging
from functools import partial

from twilio.rest import Client

from src.core.config import settings

logger = logging.getLogger(__name__)

WHATSAPP_MESSAGE_TEMPLATE = """
*Hyderabad Hangama Club - Your Ticket is Confirmed!*

Hello {name}!

Your event ticket has been confirmed.

*Ticket Code:* `{ticket_code}`

Please show this ticket code at the entrance for scanning.

We look forward to seeing you!
- Hyderabad Hangama Club Team
"""


async def send_ticket_whatsapp(
      phone: str,
      name: str,
      ticket_code: str,
) -> None:
      """
          Send WhatsApp message with ticket code via Twilio.

              Phone number should be in E.164 format: +919876543210
                  """
      # Normalize phone number to WhatsApp format
      if not phone.startswith("+"):
                phone = f"+{phone}"
            to_whatsapp = f"whatsapp:{phone}"

    message_body = WHATSAPP_MESSAGE_TEMPLATE.format(
              name=name,
              ticket_code=ticket_code,
    )

    # Run sync Twilio SDK in thread pool
    loop = asyncio.get_event_loop()
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    send_fn = partial(
              client.messages.create,
              from_=settings.TWILIO_WHATSAPP_FROM,
              to=to_whatsapp,
              body=message_body,
    )

    message = await loop.run_in_executor(None, send_fn)
    logger.info(f"WhatsApp sent to {phone} | SID: {message.sid} | Ticket: {ticket_code}")
