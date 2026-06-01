# Environment Variables - Hyderabad Hangama Club

Use `apps/api/.env` and `apps/web/.env.local` locally. Copy from `.env.example` files.

**Production:** see [DEPLOYMENT.md](DEPLOYMENT.md) for Vercel + public API setup.

## Application (API)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| APP_NAME | No | Hyderabad Hangama Club | Application name |
| APP_ENV | No | development | `development` / `staging` / `production` |
| DEBUG | No | false | Enable debug (set `false` in production) |
| SECRET_KEY | YES | - | Min 32-char secret |

## Database (API)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DATABASE_URL | YES | - | `postgresql+asyncpg://...` (`postgres://` from Render is auto-converted) |
| REDIS_URL | No | redis://localhost:6379/0 | Redis URL |

## CORS & public URLs (API) — required for Vercel / other devices

| Variable | Required | Description |
|----------|----------|-------------|
| API_BASE_URL | YES (prod) | Public HTTPS API URL, no trailing slash — WhatsApp QR image links |
| CORS_ORIGINS | YES (prod) | Comma-separated frontend origins, e.g. `https://app.vercel.app` |
| ADMIN_DASHBOARD_URL | YES (prod) | Full URL to admin page in notifications |

## Razorpay (API)

| Variable | Required | Description |
|----------|----------|-------------|
| RAZORPAY_KEY_ID | If RAZORPAY mode | Public key |
| RAZORPAY_KEY_SECRET | If RAZORPAY mode | Secret key |
| RAZORPAY_WEBHOOK_SECRET | If RAZORPAY mode | Webhook signature secret |

## Email — Resend (API)

| Variable | Required | Description |
|----------|----------|-------------|
| RESEND_API_KEY | YES | Resend API key |
| EMAIL_FROM | YES | Verified sender |
| EMAIL_FROM_NAME | No | Display name |

## WhatsApp (API)

| Variable | Required | Description |
|----------|----------|-------------|
| AISENSY_API_KEY | For AiSensy | Campaign WhatsApp |
| AISENSY_CAMPAIGN_NAME | No | Default `ticket_confirmation` |
| TWILIO_* | For Twilio | Alternative provider |

## Payments (API)

| Variable | Required | Description |
|----------|----------|-------------|
| PAYMENT_MODE | YES | `UPI_MANUAL` or `RAZORPAY` |
| UPI_ID | If UPI | UPI VPA |
| UPI_MERCHANT_NAME | No | Shown in UPI intent |
| ADMIN_API_KEY | YES | Protects `/admin/*` routes |
| ADMIN_WHATSAPP_NUMBER | No | Payment alert WhatsApp |
| ADMIN_EMAIL | No | Payment alert email |

## Frontend (Vercel / Next.js)

Set in **Vercel → Environment Variables** (must redeploy after changes).

| Variable | Required | Description |
|----------|----------|-------------|
| NEXT_PUBLIC_API_URL | **YES** | Public HTTPS backend URL (not localhost on Vercel) |
| NEXT_PUBLIC_ADMIN_KEY | YES | Must match API `ADMIN_API_KEY` |
| NEXT_PUBLIC_UPI_ID | If UPI | Client QR fallback; match API `UPI_ID` |
| NEXT_PUBLIC_RAZORPAY_KEY_ID | If Razorpay | Public Razorpay key |

## Security

- Never commit `.env` files
- Use different keys for test vs live
- Set `DEBUG=false` and strong `SECRET_KEY` in production
- Restrict `CORS_ORIGINS` to your real frontend domains
