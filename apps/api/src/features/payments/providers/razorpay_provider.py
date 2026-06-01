"""Razorpay payment provider — online card/wallet/UPI-express checkout."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.domain.models.registration import Event, Payment, Registration
from src.features.payments.providers.base import PaymentProvider
from src.features.registrations.schemas import PaymentOrderResponse

logger = logging.getLogger(__name__)


class RazorpayProvider(PaymentProvider):
    """Creates Razorpay orders; payment completion is verified via
    POST /payments/verify (signature) or POST /payments/webhook.
    """

    def __init__(self) -> None:
        import razorpay
        self._client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET.get_secret_value(),
            )
        )

    @property
    def mode(self) -> str:
        return "RAZORPAY"

    async def create_order(
        self,
        registration: Registration,
        event: Event,
        amount: int,
        db: AsyncSession,
    ) -> PaymentOrderResponse:
        order_data = self._client.order.create({
            "amount": amount,
            "currency": "INR",
            "receipt": str(registration.id),
            "notes": {
                "registration_id": str(registration.id),
                "event_name": event.name,
                "attendee_name": registration.name,
                "quantity": str(registration.quantity),
            },
        })

        payment = Payment(
            registration_id=registration.id,
            razorpay_order_id=order_data["id"],
            amount=amount,
            currency="INR",
            status="initiated",
            payment_method="razorpay",
        )
        db.add(payment)

        logger.info("Razorpay order created: %s", order_data["id"])

        return PaymentOrderResponse(
            razorpay_order_id=order_data["id"],
            amount=amount,
            currency="INR",
            key_id=settings.RAZORPAY_KEY_ID,
        )
