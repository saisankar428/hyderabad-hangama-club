"""
Registration Service - Application layer (Use Cases).
Orchestrates domain logic, payment initiation, and repository calls.
Follows Single Responsibility and Dependency Inversion principles.
"""

import uuid
import logging
from typing import Optional

import razorpay
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.domain.models.registration import Registration, Payment, Event
from src.features.registrations.schemas import (
    RegistrationCreate,
    RegistrationResponse,
    PaymentOrderResponse,
)

logger = logging.getLogger(__name__)


class RegistrationService:
      """Handles all registration business logic."""

    def __init__(self, db: AsyncSession) -> None:
              self._db = db
              self._razorpay = razorpay.Client(
                  auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
              )

    async def create_registration(self, payload: RegistrationCreate) -> RegistrationResponse:
              """
                      Create registration and initiate Razorpay payment order.

                              Steps:
                                      1. Validate event exists and has capacity
                                              2. Create registration record
                                                      3. Create Razorpay order
                                                              4. Create payment record
                                                                      5. Return response with order details
                                                                              """
              # 1. Validate event
              event = await self._get_event_or_raise(payload.event_id)

        # 2. Check capacity
              await self._check_capacity(event)

        # 3. Create registration
              registration = Registration(
                  event_id=payload.event_id,
                  name=payload.name,
                  email=payload.email,
                  phone=payload.phone,
                  status="payment_pending",
              )
              self._db.add(registration)
              await self._db.flush()

        # 4. Create Razorpay order
              order_data = self._razorpay.order.create({
                  "amount": event.ticket_price,
                  "currency": "INR",
                  "receipt": str(registration.id),
                  "notes": {
                      "registration_id": str(registration.id),
                      "event_name": event.name,
                      "attendee_name": payload.name,
                  },
              })

        # 5. Create payment record
              payment = Payment(
                  registration_id=registration.id,
                  razorpay_order_id=order_data["id"],
                  amount=event.ticket_price,
                  status="initiated",
              )
              self._db.add(payment)
              await self._db.commit()
              await self._db.refresh(registration)

        logger.info(f"Registration created: {registration.id} | Order: {order_data['id']}")

        return RegistrationResponse(
                      id=registration.id,
                      event_id=registration.event_id,
                      name=registration.name,
                      email=registration.email,
                      phone=registration.phone,
                      status=registration.status,
                      created_at=registration.created_at,
                      payment_order=PaymentOrderResponse(
                                        razorpay_order_id=order_data["id"],
                                        amount=event.ticket_price,
                                        currency="INR",
                                        key_id=settings.RAZORPAY_KEY_ID,
                      ),
        )

    async def get_registration(self, registration_id: uuid.UUID) -> Optional[RegistrationResponse]:
              """Get registration by ID."""
              result = await self._db.execute(
                  select(Registration).where(Registration.id == registration_id)
              )
              registration = result.scalar_one_or_none()
              if not registration:
                            return None
                        return RegistrationResponse.model_validate(registration)

    async def _get_event_or_raise(self, event_id: uuid.UUID) -> Event:
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

    async def _check_capacity(self, event: Event) -> None:
              from sqlalchemy import func as sqlfunc
        result = await self._db.execute(
                      select(sqlfunc.count()).select_from(Registration).where(
                                        Registration.event_id == event.id,
                                        Registration.status.in_(["confirmed", "payment_pending"]),
                      )
        )
        count = result.scalar_one()
        if count >= event.capacity:
                      from fastapi import HTTPException, status
                      raise HTTPException(
                          status_code=status.HTTP_409_CONFLICT,
                          detail="Event is fully booked",
                      )
