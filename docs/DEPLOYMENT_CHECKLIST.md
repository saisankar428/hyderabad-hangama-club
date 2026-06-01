# Production Deployment Checklist

**Stack:** Vercel Free · Render Free · Supabase PostgreSQL · Supabase Storage  
**Status:** Planning — execute after [DEPLOYMENT_PLAN.md](./DEPLOYMENT_PLAN.md) approval  
**Legend:** `[ ]` todo · `[~]` in progress · `[x]` done

---

## Priority P0 — Blockers (must complete before real users)

### Accounts & projects

- [ ] **P0-1** Create Supabase project (choose region near users)
- [ ] **P0-2** Save Supabase database password and project URL securely
- [ ] **P0-3** Create Render account and connect GitHub repository
- [ ] **P0-4** Confirm Vercel project exists (`hyderabadhangamaclub.vercel.app`) with **Root Directory** = `apps/web`

### Supabase PostgreSQL

- [ ] **P0-5** Copy connection string (Session or Direct; test Transaction pooler if preferred)
- [ ] **P0-6** Decide connection string format for Render `DATABASE_URL` (`postgresql+asyncpg://...`)
- [ ] **P0-7** Approve + implement **SSL support** in `apps/api/src/core/database.py` for Supabase
- [ ] **P0-8** Deploy API once; verify `GET /health/db` returns `"database": "connected"`
- [ ] **P0-9** Confirm tables created (`events`, `registrations`, `payments`, `tickets`) via Supabase Table Editor
- [ ] **P0-10** Verify seed event **Tollywood Jam Night** exists (or insert manually)

### Supabase Storage (code change required)

- [ ] **P0-11** Approve + implement Supabase Storage upload module (`infrastructure/storage.py`)
- [ ] **P0-12** Create bucket `payment-screenshots` (or chosen name)
- [ ] **P0-13** Configure bucket policy (service role write; public read OR signed URL strategy)
- [ ] **P0-14** Add env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_STORAGE_BUCKET`
- [ ] **P0-15** Replace `_save_screenshot()` local disk write with Storage upload
- [ ] **P0-16** Store **HTTPS URL** in `payments.payment_screenshot_url`
- [ ] **P0-17** Disable or production-gate local `/uploads` StaticFiles mount
- [ ] **P0-18** Test UPI flow: upload screenshot from phone → visible in `/admin`

### Render API service

- [ ] **P0-19** Create Render Web Service from `apps/api/Dockerfile` (Docker, Free plan)
- [ ] **P0-20** Set `APP_ENV=production`, `DEBUG=false`
- [ ] **P0-21** Generate and set strong `SECRET_KEY` (32+ chars)
- [ ] **P0-22** Set `DATABASE_URL` to Supabase URI (not Render Postgres)
- [ ] **P0-23** Set `API_BASE_URL=https://<render-service>.onrender.com`
- [ ] **P0-24** Set `CORS_ORIGINS=https://hyderabadhangamaclub.vercel.app`
- [ ] **P0-25** Set `ADMIN_DASHBOARD_URL=https://hyderabadhangamaclub.vercel.app/admin`
- [ ] **P0-26** Set `ADMIN_API_KEY` (strong); mirror on Vercel as `NEXT_PUBLIC_ADMIN_KEY`
- [ ] **P0-27** Set `PAYMENT_MODE`, `UPI_ID`, `UPI_MERCHANT_NAME` (if UPI)
- [ ] **P0-28** Configure health check path `/health/`
- [ ] **P0-29** Deploy API; note public URL for next steps

### Vercel frontend

- [ ] **P0-30** Set `NEXT_PUBLIC_API_URL` = Render API HTTPS URL (Production + Preview)
- [ ] **P0-31** Set `NEXT_PUBLIC_ADMIN_KEY` = same as API `ADMIN_API_KEY`
- [ ] **P0-32** Set `NEXT_PUBLIC_UPI_ID` = same as API `UPI_ID` (if UPI)
- [ ] **P0-33** **Redeploy** Vercel (required — env vars bake at build time)
- [ ] **P0-34** Confirm production JS bundle does **not** contain `localhost:8000`

### End-to-end smoke test (production)

- [ ] **P0-35** Mobile: open `/register` — event loads from API (not stuck on “Loading…”)
- [ ] **P0-36** Complete registration + UPI payment + screenshot upload
- [ ] **P0-37** Admin receives WhatsApp/email alert (if AiSensy/Resend configured)
- [ ] **P0-38** Admin: `/admin` — pending payment visible with screenshot
- [ ] **P0-39** Admin: confirm payment → ticket email/WhatsApp received
- [ ] **P0-40** Scanner: `/scanner` — scan ticket QR → entry granted
- [ ] **P0-41** Re-scan same ticket → “already used”

---

## Priority P1 — Production correctness (soon after P0)

### External services

- [ ] **P1-1** Resend: verify `EMAIL_FROM` domain
- [ ] **P1-2** Set `RESEND_API_KEY` on Render
- [ ] **P1-3** AiSensy: configure `ticket_confirmation` campaign
- [ ] **P1-4** Set `AISENSY_API_KEY` on Render
- [ ] **P1-5** Set `ADMIN_WHATSAPP_NUMBER` and `ADMIN_EMAIL` for payment alerts
- [ ] **P1-6** (Optional) Razorpay live keys + webhook URL if switching to `RAZORPAY`

### Configuration & docs

- [ ] **P1-7** Update `render.yaml` — remove Render Postgres; document Supabase manual secrets
- [ ] **P1-8** Update `docs/ENV.md` with Supabase variables
- [ ] **P1-9** Fix `docs/API.md` incorrect `/api/v1` prefix
- [ ] **P1-10** Update `docs/ARCHITECTURE.md` (Resend vs SendGrid, Storage, no Redis usage)

### CI/CD

- [ ] **P1-11** Fix `.github/workflows/ci.yml` formatting; use Resend vars not SendGrid
- [ ] **P1-12** CI: add Supabase-less integration test or mock Storage in tests
- [ ] **P1-13** Enable Render auto-deploy on `main` (optional)

### API hardening (small code changes)

- [ ] **P1-14** Add `pending_verification` to payment status enum
- [ ] **P1-15** Startup validation: fail fast in production if `API_BASE_URL` / `CORS_ORIGINS` missing

---

## Priority P2 — Security & operability (before high-traffic event)

- [ ] **P2-1** Replace client-exposed `NEXT_PUBLIC_ADMIN_KEY` with server-side admin API proxy (Next.js Route Handlers)
- [ ] **P2-2** Add Alembic migrations; stop relying on `create_all` + raw ALTER at startup
- [ ] **P2-3** Protect `POST /events/` (admin-only or remove public create)
- [ ] **P2-4** Rate limit `/payments/submit-utr` and `/scanner/scan`
- [ ] **P2-5** Add error monitoring (e.g. Sentry) on API + Web
- [ ] **P2-6** Document Render cold-start mitigation (ping job or paid plan)
- [ ] **P2-7** Backup strategy: Supabase point-in-time / manual export before event
- [ ] **P2-8** Runbook for event day (admin confirm SLA, scanner offline fallback)

---

## Priority P3 — Optional enhancements (lowest)

- [ ] **P3-1** Custom domain on Vercel; update CORS + `ADMIN_DASHBOARD_URL`
- [ ] **P3-2** Vercel Preview environments pointing to staging API
- [ ] **P3-3** Staging Render service + staging Supabase project
- [ ] **P3-4** Remove unused Redis from `docker-compose.yml` or implement caching
- [ ] **P3-5** Move ticket QR out of DB base64 to Storage (if size becomes an issue)
- [ ] **P3-6** GitHub Action post-deploy smoke: `curl /health/db` + `/events`
- [ ] **P3-7** Admin dashboard auth UI improvements (session, not localStorage key)

---

## Quick reference — env sync matrix

| Value | Render (API) | Vercel (Web) | Supabase |
|-------|--------------|--------------|----------|
| Public API URL | `API_BASE_URL` | `NEXT_PUBLIC_API_URL` | — |
| Admin secret | `ADMIN_API_KEY` | `NEXT_PUBLIC_ADMIN_KEY` | — |
| UPI ID | `UPI_ID` | `NEXT_PUBLIC_UPI_ID` | — |
| Frontend origin | `CORS_ORIGINS` | — | — |
| Admin link in notifications | `ADMIN_DASHBOARD_URL` | — | — |
| DB connection | `DATABASE_URL` | — | Connection string |
| Screenshots | `SUPABASE_*` | — | Bucket + policies |
| Email/WhatsApp | `RESEND_*`, `AISENSY_*` | — | — |

---

## Sign-off

| Role | Name | Date | Approved |
|------|------|------|----------|
| Product / Owner | | | [ ] |
| Engineering | | | [ ] |

**After sign-off:** begin P0 code changes per [DEPLOYMENT_PLAN.md](./DEPLOYMENT_PLAN.md) §8.
