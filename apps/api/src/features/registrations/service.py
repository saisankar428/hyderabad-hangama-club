"""Registration Service — orchestrates domain logic, payment initiation, and DB writes."""

import logging
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.registration import Event, Registration
from src.features.payments.providers import get_payment_provider
from src.features.registrations.schemas import RegistrationCreate, RegistrationResponse

logger = logging.getLogger(__name__)


class RegistrationService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_registration(self, payload: RegistrationCreate) -> RegistrationResponse:
        event = await self._get_event_or_raise(payload.event_id)
        await self._check_capacity(event, payload.quantity)

        registration = Registration(
            event_id=payload.event_id,
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            whatsapp=payload.whatsapp or payload.phone,
            quantity=payload.quantity,
            notes=payload.notes,
            status="payment_pending",
        )
        self._db.add(registration)
        await self._db.flush()

        amount = event.ticket_price * payload.quantity
        provider = get_payment_provider()
        payment_order = await provider.create_order(registration, event, amount, self._db)

        await self._db.commit()
        await self._db.refresh(registration)

        logger.info(
            "Registration created: %s | provider: %s", registration.id, provider.mode
        )

        return RegistrationResponse(
            id=registration.id,
            event_id=registration.event_id,
            name=registration.name,
            email=registration.email,
            phone=registration.phone,
            whatsapp=registration.whatsapp,
            quantity=registration.quantity,
            notes=registration.notes,
            status=registration.status,
            created_at=registration.created_at,
            payment_order=payment_order,
        )

    async def get_registration(self, registration_id: str) -> Optional[RegistrationResponse]:
        result = await self._db.execute(
            select(Registration).where(Registration.id == registration_id)
        )
        registration = result.scalar_one_or_none()
        if not registration:
            return None
        return RegistrationResponse.model_validate(registration)

    async def _get_event_or_raise(self, event_id: str) -> Event:
        result = await self._db.execute(
            select(Event).where(Event.id == event_id, Event.is_active == True)
        )
        event = result.scalar_one_or_none()
        if not event:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found or inactive",
            )
        return event

    async def _check_capacity(self, event: Event, quantity: int) -> None:
        result = await self._db.execute(
            select(func.coalesce(func.sum(Registration.quantity), 0)).where(
                Registration.event_id == event.id,
                Registration.status.in_(["confirmed", "payment_pending"]),
            )
        )
        count = result.scalar_one() or 0
        if count + quantity > event.capacity:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Event does not have enough available tickets",
            )
