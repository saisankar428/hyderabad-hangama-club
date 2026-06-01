"""Pydantic schemas for Registrations feature - request/response validation."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegistrationCreate(BaseModel):
    """Schema for creating a new registration."""

    event_id: uuid.UUID = Field(..., description="UUID of the event to register for")
    name: str = Field(..., min_length=2, max_length=255, description="Full name of attendee")
    email: EmailStr = Field(..., description="Email address for ticket delivery")
    phone: str = Field(..., min_length=10, max_length=20, description="Phone number for WhatsApp")
    quantity: int = Field(1, gt=0, le=10, description="Number of tickets to purchase")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
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
                "phone": "+919876543210",
                "quantity": 2,
            }
        }
    }


class PaymentOrderResponse(BaseModel):
    """Razorpay order details returned after registration."""

    razorpay_order_id: str
    amount: int = Field(..., description="Amount in paise")
    currency: str = Field(default="INR")
    key_id: str = Field(..., description="Razorpay public key ID")


class RegistrationResponse(BaseModel):
    """Schema for registration response."""

    id: uuid.UUID
    event_id: uuid.UUID
    name: str
    email: str
    phone: str
    quantity: int
    status: str
    created_at: datetime
    payment_order: Optional[PaymentOrderResponse] = None

    model_config = {"from_attributes": True}


class PaymentVerifyRequest(BaseModel):
    """Schema for verifying Razorpay payment signature."""

    registration_id: uuid.UUID
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
