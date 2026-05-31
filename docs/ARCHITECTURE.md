# Architecture - Hyderabad Hangama Club

## System Overview

```
User Browser
    |
    v
[Next.js 15 Frontend - Port 3000]
    |
    v (via Nginx reverse proxy - Port 80)
    |
[FastAPI Backend - Port 8000]
    |
    +---> [PostgreSQL DB - Port 5432]
    +---> [Redis Cache - Port 6379]
    +---> [Razorpay API] (Payments)
    +---> [SendGrid API] (Email)
    +---> [Twilio API]   (WhatsApp)
```

## User Flow

```
1. User visits event page
        |
2. Fills registration form (name, email, phone)
        |
3. POST /api/v1/registrations
        |
4. FastAPI creates Registration record
        |
5. FastAPI creates Razorpay Order
        |
6. Returns order_id + key_id to frontend
        |
7. Razorpay payment modal opens
        |
8. User completes payment
        |
9. POST /api/v1/payments/verify (with signature)
        |
10. FastAPI verifies HMAC signature
        |
11. Registration marked CONFIRMED
        |
12. QR Ticket generated (ticket_code + QR PNG)
        |
13. Email sent via SendGrid (with QR inline)
        |
14. WhatsApp sent via Twilio
        |
15. Redirect to success page with ticket
        |
16. [At Event] Staff scans QR code
        |
17. POST /api/v1/scanner/scan
        |
18. FastAPI validates + marks ticket USED
        |
19. Entry granted / denied response
```

## Clean Architecture Layers

```
apps/api/src/
+-- core/           # Framework config (DB, settings)
+-- domain/
|   +-- models/     # SQLAlchemy entities (pure domain)
+-- features/       # Feature-based vertical slices
|   +-- events/
|   |   +-- router.py    # Interface layer (HTTP)
|   +-- registrations/
|   |   +-- router.py    # Interface layer
|   |   +-- schemas.py   # DTOs (Pydantic)
|   |   +-- service.py   # Application layer (use cases)
|   +-- payments/
|   +-- tickets/
|   +-- scanner/
|   +-- health/
+-- infrastructure/  # External adapters
    +-- email.py     # SendGrid adapter
    +-- whatsapp.py  # Twilio adapter
    +-- logging.py   # Structured logging
```

## SOLID Principles Applied

| Principle | Implementation |
|-----------|---------------|
| **S**ingle Responsibility | Each service handles one feature domain |
| **O**pen/Closed | New features added as new feature modules |
| **L**iskov Substitution | Services injectable via interfaces |
| **I**nterface Segregation | Schemas separate from domain models |
| **D**ependency Inversion | DB session injected, not created in services |

## Database Schema

```
events
  id (UUID PK)
  name, description, venue
  event_date, capacity, ticket_price
  is_active, created_at, updated_at

registrations
  id (UUID PK)
  event_id (FK -> events)
  name, email, phone
  status (pending|payment_pending|confirmed|cancelled)
  created_at, updated_at

payments
  id (UUID PK)
  registration_id (FK -> registrations)
  razorpay_order_id (unique)
  razorpay_payment_id, razorpay_signature
  amount, currency, status
  created_at, updated_at

tickets
  id (UUID PK)
  registration_id (FK -> registrations, unique)
  ticket_code (unique, indexed)
  qr_code_url
  status (active|used|expired|cancelled)
  scanned_at
  email_sent, whatsapp_sent
  created_at
```

## Technology Decisions

| Decision | Choice | Rationale |
|---------|--------|-----------|
| Async ORM | SQLAlchemy 2.0 async | Non-blocking DB operations |
| Validation | Pydantic v2 | Type-safe, fast validation |
| QR Generation | qrcode + Pillow | Lightweight, no external service |
| Payment | Razorpay | India-first, UPI support |
| Email | SendGrid | Reliable, template support |
| WhatsApp | Twilio | Official Business API support |
