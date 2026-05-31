"""Registrations feature router - Clean Architecture interface layer."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.features.registrations.schemas import RegistrationCreate, RegistrationResponse
from src.features.registrations.service import RegistrationService

router = APIRouter(prefix="/registrations")


def get_registration_service(db: Annotated[AsyncSession, Depends(get_db)]) -> RegistrationService:
      return RegistrationService(db)


@router.post(
      "/",
      response_model=RegistrationResponse,
      status_code=status.HTTP_201_CREATED,
      summary="Register for an event",
      description="Create a new event registration and initiate payment.",
)
async def create_registration(
      payload: RegistrationCreate,
      service: Annotated[RegistrationService, Depends(get_registration_service)],
) -> RegistrationResponse:
      """Register attendee for an event and create Razorpay order."""
      return await service.create_registration(payload)


@router.get(
      "/{registration_id}",
      response_model=RegistrationResponse,
      summary="Get registration by ID",
)
async def get_registration(
      registration_id: uuid.UUID,
      service: Annotated[RegistrationService, Depends(get_registration_service)],
) -> RegistrationResponse:
      """Retrieve a registration by its UUID."""
      registration = await service.get_registration(registration_id)
      if not registration:
                raise HTTPException(
                              status_code=status.HTTP_404_NOT_FOUND,
                              detail=f"Registration {registration_id} not found",
                )
            return registration
