from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from src.core.config import settings
from src.core.database import Base, async_session, engine
from src.domain.models.registration import Event
from src.features.admin.router import router as admin_router
from src.features.events.router import router as events_router
from src.features.health.router import router as health_router
from src.features.orders.router import router as orders_router
from src.features.payments.router import router as payments_router
from src.features.registrations.router import router as registrations_router
from src.features.scanner.router import router as scanner_router
from src.features.tickets.router import router as tickets_router

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(events_router)
app.include_router(registrations_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(tickets_router)
app.include_router(scanner_router)
app.include_router(admin_router)


@app.on_event("startup")
async def startup_event() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        event_name = "Tollywood Jam Night"
        result = await session.execute(select(Event).where(Event.name == event_name))
        event = result.scalar_one_or_none()
        if not event:
            event = Event(
                name=event_name,
                description="A night of Tollywood music, lights, and live performances at Roast & Toast Lounge.",
                venue="Roast & Toast Lounge",
                event_date=datetime(2026, 6, 6, 17, 0, tzinfo=timezone(timedelta(hours=5, minutes=30))),
                capacity=100,
                ticket_price=29900,  # ₹299
                is_active=True,
            )
            session.add(event)
            await session.commit()


@app.get("/")
async def root() -> dict:
    return {"message": "Hyderabad Hangama Club API is running"}
