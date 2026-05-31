"""Events feature router - CRUD for event management."""

import uuid
from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.domain.models.registration import Event

router = APIRouter(prefix="/events")


class EventCreate(BaseModel):
      name: str = Field(..., min_length=3, max_length=255)
      description: Optional[str] = None
      venue: str = Field(..., min_length=3, max_length=500)
      event_date: datetime
      capacity: int = Field(..., gt=0, le=10000)
      ticket_price: int = Field(..., gt=0, description="Price in paise (INR)")


class EventResponse(BaseModel):
      id: uuid.UUID
      name: str
      description: Optional[str]
      venue: str
      event_date: datetime
      capacity: int
      ticket_price: int
      is_active: bool
      created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/", response_model=List[EventResponse], summary="List all active events")
async def list_events(db: Annotated[AsyncSession, Depends(get_db)]) -> List[EventResponse]:
      result = await db.execute(select(Event).where(Event.is_active == True))
      events = result.scalars().all()
      return [EventResponse.model_validate(e) for e in events]


@router.get("/{event_id}", response_model=EventResponse, summary="Get event by ID")
async def get_event(
      event_id: uuid.UUID,
      db: Annotated[AsyncSession, Depends(get_db)],
) -> EventResponse:
      result = await db.execute(select(Event).where(Event.id == event_id))
      event = result.scalar_one_or_none()
      if not event:
                raise HTTPException(status_code=404, detail="Event not found")
            return EventResponse.model_validate(event)


@router.post("/", response_model=EventResponse, status_code=201, summary="Create event")
async def create_event(
      payload: EventCreate,
      db: Annotated[AsyncSession, Depends(get_db)],
) -> EventResponse:
      event = Event(**payload.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return EventResponse.model_validate(event)
