"""UPI manual payment provider — QR + UTR + admin approval workflow."""

import logging
import uuid
from urllib.parse import quote

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.domain.models.registration import Event, Payment, Registration
from src.features.payments.providers.base import PaymentProvider
from src.features.registrations.schemas import UpiPaymentOrderResponse
from src.features.tickets.service import generate_qr_code_base64

logger = logging.getLogger(__name__)


class UpiManualProvider(PaymentProvider):
    """Creates UPI deep-link orders; payment completion requires the attendee
    to submit their UTR via POST /payments/submit-utr, then admin approval via
    POST /admin/payments/{id}/confirm which triggers ticket generation.
    """

    @property
    def mode(self) -> str:
        return "UPI_MANUAL"

    async def create_order(
        self,
        registration: Registration,
        event: Event,
        amount: int,
        db: AsyncSession,
    ) -> UpiPaymentOrderResponse:
        order_ref = f"UPI-{uuid.uuid4().hex[:12].upper()}"
        amount_rupees = amount / 100

        upi_params = [
            ("pa", settings.UPI_ID),
            ("pn", settings.UPI_MERCHANT_NAME),
            ("am", f"{amount_rupees:.2f}"),
            ("tn", f"HHC Ticket - {registration.quantity} ticket(s)"),
            ("tr", order_ref),
            ("cu", "INR"),
        ]
        upi_link = "upi://pay?" + "&".join(
            f"{k}={quote(str(v))}" for k, v in upi_params
        )
        upi_qr_base64 = generate_qr_code_base64(upi_link)

        payment = Payment(
            registration_id=registration.id,
            razorpay_order_id=order_ref,
            amount=amount,
            currency="INR",
            status="initiated",
            payment_method="upi",
        )
        db.add(payment)

        logger.info("UPI order created: %s for registration %s", order_ref, registration.id)

        return UpiPaymentOrderResponse(
            order_ref=order_ref,
            amount=amount,
            currency="INR",
            upi_id=settings.UPI_ID,
            upi_link=upi_link,
            upi_qr_base64=upi_qr_base64,
        )
