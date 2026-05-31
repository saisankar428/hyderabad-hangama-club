# Environment Variables - Hyderabad Hangama Club

All variables should be set in `apps/api/.env` and `apps/web/.env.local`.
Use `.env.example` as template.

## Application

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| APP_NAME | No | Hyderabad Hangama Club | Application name |
| APP_ENV | No | development | Environment: development/staging/production |
| DEBUG | No | true | Enable debug mode (set false in production) |
| SECRET_KEY | YES | - | Min 32-char secret for JWT/security |

## Database

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DATABASE_URL | YES | - | PostgreSQL async URL: postgresql+asyncpg://user:pass@host:5432/db |
| POSTGRES_DB | No | hangama | Database name (for Docker) |
| POSTGRES_USER | No | hangama | Database user (for Docker) |
| POSTGRES_PASSWORD | No | - | Database password (for Docker) |
| DB_POOL_SIZE | No | 10 | SQLAlchemy connection pool size |
| DB_MAX_OVERFLOW | No | 20 | SQLAlchemy max overflow connections |

## Redis

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| REDIS_URL | No | redis://localhost:6379/0 | Redis connection URL |

## Razorpay (Payment Gateway)

Get keys from: https://dashboard.razorpay.com/app/keys

| Variable | Required | Description |
|----------|----------|-------------|
| RAZORPAY_KEY_ID | YES | Public key (starts with rzp_test_ or rzp_live_) |
| RAZORPAY_KEY_SECRET | YES | Secret key |
| RAZORPAY_WEBHOOK_SECRET | YES | Webhook signature secret |

Use test keys for development, live keys for production.

## SendGrid (Email)

Get API key from: https://app.sendgrid.com/settings/api_keys

| Variable | Required | Description |
|----------|----------|-------------|
| SENDGRID_API_KEY | YES | SendGrid API key (starts with SG.) |
| EMAIL_FROM | YES | Verified sender email address |
| EMAIL_FROM_NAME | No | Sender display name |

Sender email must be verified in SendGrid dashboard.

## Twilio (WhatsApp)

Get credentials from: https://console.twilio.com

| Variable | Required | Description |
|----------|----------|-------------|
| TWILIO_ACCOUNT_SID | YES | Account SID (starts with AC) |
| TWILIO_AUTH_TOKEN | YES | Auth token |
| TWILIO_WHATSAPP_FROM | No | WhatsApp sender (default: Twilio sandbox) |

For production, use Twilio WhatsApp Business API.

## Frontend (Next.js)

| Variable | Required | Description |
|----------|----------|-------------|
| NEXT_PUBLIC_API_URL | YES | Backend API URL |
| NEXT_PUBLIC_RAZORPAY_KEY_ID | YES | Razorpay public key (exposed to browser) |
| NEXT_PUBLIC_APP_NAME | No | App name for UI |

## Security Notes

- Never commit `.env` files to git (already in `.gitignore`)
- - Rotate `SECRET_KEY` if compromised
  - - Use different Razorpay keys for test vs production
    - - Set `DEBUG=false` in production
      - - Use strong, unique passwords for database
