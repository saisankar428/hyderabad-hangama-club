from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.features.registrations.schemas import RegistrationCreate, RegistrationResponse
from src.features.registrations.service import RegistrationService

router = APIRouter()


@router.post(
    "/create-order",
    response_model=RegistrationResponse,
    status_code=201,
    summary="Create a Razorpay order and register an attendee",
)
async def create_order(
    payload: RegistrationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RegistrationResponse:
    service = RegistrationService(db)
    return await service.create_registration(payload)
