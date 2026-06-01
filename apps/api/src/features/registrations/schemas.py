"""Pydantic schemas for Registrations feature — request/response validation."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegistrationCreate(BaseModel):
    event_id: uuid.UUID = Field(..., description="UUID of the event to register for")
    name: str = Field(..., min_length=2, max_length=255, description="Full name of attendee")
    email: EmailStr = Field(..., description="Email address for ticket delivery")
    phone: str = Field(..., min_length=10, max_length=20, description="Mobile number")
    whatsapp: Optional[str] = Field(None, max_length=20, description="WhatsApp number (defaults to phone if omitted)")
    quantity: int = Field(1, gt=0, le=10, description="Number of tickets to purchase")
    notes: Optional[str] = Field(None, max_length=1000, description="Special requests or notes")

    @field_validator("phone", "whatsapp", mode="before")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        digits = "".join(filter(str.isdigit, v))
        if len(digits) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Ravi Kumar",
                "email": "ravi@example.com",
                "phone": "9876543210",
                "whatsapp": "9876543210",
                "quantity": 2,
                "notes": "Vegetarian food preferred",
            }
        }
    }


class PaymentOrderResponse(BaseModel):
    razorpay_order_id: str
    amount: int = Field(..., description="Amount in paise")
    currency: str = Field(default="INR")
    key_id: str = Field(..., description="Razorpay public key ID")


class RegistrationResponse(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    name: str
    email: str
    phone: str
    whatsapp: Optional[str] = None
    quantity: int
    notes: Optional[str] = None
    status: str
    created_at: datetime
    payment_order: Optional[PaymentOrderResponse] = None

    model_config = {"from_attributes": True}


class PaymentVerifyRequest(BaseModel):
    registration_id: uuid.UUID
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
