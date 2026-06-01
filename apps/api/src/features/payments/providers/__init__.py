"""Payment provider factory.

Usage
-----
    from src.features.payments.providers import get_payment_provider

    provider = get_payment_provider()          # returns cached singleton
    order = await provider.create_order(...)
"""

from functools import lru_cache

from src.features.payments.providers.base import PaymentProvider

_SUPPORTED_MODES = ("RAZORPAY", "UPI_MANUAL")


@lru_cache(maxsize=1)
def get_payment_provider() -> PaymentProvider:
    """Return the active PaymentProvider based on PAYMENT_MODE.

    Result is cached for the process lifetime — switching modes requires
    a restart (or ``get_payment_provider.cache_clear()`` in tests).

    Raises:
        ValueError: If PAYMENT_MODE is not one of the supported values.
    """
    from src.core.config import settings  # deferred to avoid circular import at module load

    mode = settings.PAYMENT_MODE.upper()

    if mode == "RAZORPAY":
        from src.features.payments.providers.razorpay_provider import RazorpayProvider
        return RazorpayProvider()

    if mode == "UPI_MANUAL":
        from src.features.payments.providers.upi_manual_provider import UpiManualProvider
        return UpiManualProvider()

    raise ValueError(
        f"Unsupported PAYMENT_MODE='{settings.PAYMENT_MODE}'. "
        f"Supported values: {', '.join(_SUPPORTED_MODES)}"
    )


__all__ = ["PaymentProvider", "get_payment_provider"]
