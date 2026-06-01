"""Payment provider abstraction — strategy pattern."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Union

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.registration import Event, Registration

if TYPE_CHECKING:
    from src.features.registrations.schemas import PaymentOrderResponse, UpiPaymentOrderResponse


class PaymentProvider(ABC):
    """Abstract payment provider.

    Implement this class to add a new payment method.
    Only ``create_order`` and ``mode`` are required — completion flows
    (webhook, verification, or manual approval) are handled by the
    payments router with per-mode guards.

    To add a new provider:
      1. Subclass PaymentProvider and implement create_order + mode.
      2. Register in providers/__init__.py factory.
      3. Set PAYMENT_MODE env var to the new mode string.
      No other files need changing.
    """

    @property
    @abstractmethod
    def mode(self) -> str:
        """Canonical mode name matching PAYMENT_MODE env var, e.g. ``RAZORPAY``."""
        ...

    @abstractmethod
    async def create_order(
        self,
        registration: Registration,
        event: Event,
        amount: int,
        db: AsyncSession,
    ) -> "Union[PaymentOrderResponse, UpiPaymentOrderResponse]":
        """Create a payment order, persist a Payment record, return the order response.

        Args:
            registration: The freshly-flushed Registration row.
            event: The event being registered for.
            amount: Total amount in paise.
            db: Active async DB session (do not commit here — caller commits).
        """
        ...
