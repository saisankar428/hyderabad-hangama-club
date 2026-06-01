"""WhatsApp infrastructure — Twilio integration for ticket delivery."""

import asyncio
import logging
from functools import partial

from twilio.rest import Client

from src.core.config import settings

logger = logging.getLogger(__name__)

_MESSAGE_TEMPLATE = """
*Hyderabad Hangama Club — Your Ticket is Confirmed!*

Hello {name}!

Your ticket has been confirmed.

*Ticket Code:* `{ticket_code}`

Show this code at the entrance for scanning.

See you there!
— Hyderabad Hangama Club Team
"""


async def send_ticket_whatsapp(
    phone: str,
    name: str,
    ticket_code: str,
) -> None:
    if not phone.startswith("+"):
        phone = f"+{phone}"
    to_whatsapp = f"whatsapp:{phone}"

    message_body = _MESSAGE_TEMPLATE.format(name=name, ticket_code=ticket_code)

    loop = asyncio.get_event_loop()
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    send_fn = partial(
        client.messages.create,
        from_=settings.TWILIO_WHATSAPP_FROM,
        to=to_whatsapp,
        body=message_body,
    )
    message = await loop.run_in_executor(None, send_fn)
    logger.info("WhatsApp sent | phone=%s | sid=%s | ticket=%s", phone, message.sid, ticket_code)
