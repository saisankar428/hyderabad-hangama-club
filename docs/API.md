# API Reference - Hyderabad Hangama Club

Base URL: `http://localhost:8000/api/v1`
Interactive docs: `http://localhost:8000/docs`

## Authentication

Currently open API (add JWT auth for admin endpoints in production).

---

## Health

### GET /health/
Returns service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "Hyderabad Hangama Club",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Events

### GET /events/
List all active events.

### GET /events/{event_id}
Get event by UUID.

### POST /events/
Create a new event.

**Request:**
```json
{
  "name": "Hyderabad Hangama Night",
  "description": "Epic night of music and dance",
  "venue": "Hitech City Convention Center, Hyderabad",
  "event_date": "2024-12-31T20:00:00+05:30",
  "capacity": 500,
  "ticket_price": 50000
}
```

---

## Registrations

### POST /registrations/
Register for an event and initiate payment.

**Request:**
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Ravi Kumar",
  "email": "ravi@example.com",
  "phone": "+919876543210"
}
```

**Response:**
```json
{
  "id": "uuid",
  "event_id": "uuid",
  "name": "Ravi Kumar",
  "email": "ravi@example.com",
  "phone": "+919876543210",
  "status": "payment_pending",
  "created_at": "2024-01-15T10:30:00Z",
  "payment_order": {
    "razorpay_order_id": "order_xxxx",
    "amount": 50000,
    "currency": "INR",
    "key_id": "rzp_test_xxx"
  }
}
```

### GET /registrations/{registration_id}
Get registration details.

---

## Payments

### POST /payments/verify
Verify Razorpay payment and generate ticket.

**Request:**
```json
{
  "registration_id": "uuid",
  "razorpay_order_id": "order_xxxx",
  "razorpay_payment_id": "pay_xxxx",
  "razorpay_signature": "hmac_signature"
}
```

**Response:**
```json
{
  "status": "success",
  "ticket_code": "HHC-A3X9K2P7M1Q5"
}
```

### POST /payments/webhook
Razorpay webhook handler (signature required in header).

---

## Tickets

### GET /tickets/{ticket_code}
Get ticket details by code.

**Response:**
```json
{
  "id": "uuid",
  "registration_id": "uuid",
  "ticket_code": "HHC-A3X9K2P7M1Q5",
  "qr_code_url": "data:image/png;base64,...",
  "status": "active",
  "scanned_at": null,
  "email_sent": true,
  "whatsapp_sent": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## Scanner

### POST /scanner/scan
Scan a QR ticket at event entrance.

**Request:**
```json
{
  "ticket_code": "HHC-A3X9K2P7M1Q5"
}
```

**Response (valid):**
```json
{
  "valid": true,
  "ticket_code": "HHC-A3X9K2P7M1Q5",
  "attendee_name": "Ravi Kumar",
  "event_id": "uuid",
  "message": "Welcome, Ravi Kumar! Entry granted.",
  "already_scanned": false
}
```

**Response (already used):**
```json
{
  "valid": false,
  "ticket_code": "HHC-A3X9K2P7M1Q5",
  "attendee_name": "Ravi Kumar",
  "event_id": "uuid",
  "message": "Ticket already used at 2024-12-31T21:05:00Z",
  "already_scanned": true
}
```

---

## Error Responses

All errors follow RFC 9110:

```json
{
  "detail": "Human-readable error message"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request / validation error |
| 404 | Resource not found |
| 409 | Conflict (e.g. event full) |
| 422 | Unprocessable entity (schema validation) |
| 500 | Internal server error |
