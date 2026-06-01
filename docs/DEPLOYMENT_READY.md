# Deployment Ready Guide

This document reflects the **implemented** production stack:

| Component | Provider |
|-----------|----------|
| Frontend | Vercel Free (`apps/web`) |
| Backend API | Render Free (`apps/api`) |
| Database | Supabase PostgreSQL |
| Screenshots | Supabase Storage (public bucket) |

---

## What was implemented in code

- **Supabase PostgreSQL** — SSL-aware async engine, `NullPool` auto-enabled for transaction pooler (port 6543)
- **Supabase Storage** — `upload_file`, `delete_file`, `get_public_url` in `apps/api/src/infrastructure/storage.py`
- **Payment screenshots** — uploaded to Supabase; DB stores public HTTPS URL
- **Health** — `GET /health`, `GET /health/`, `GET /health/db`
- **CORS** — configurable via `CORS_ORIGINS`; production startup fails if `*`
- **Logging** — structured stdout logging via `logging_config.py`
- **Production guards** — startup validates required env vars when `APP_ENV=production`
- **Local dev** — local `/uploads` only when not production and Supabase not configured

---

## Manual setup (required before go-live)

### 1. Supabase

1. Create project → note **Project URL** and **service_role** key.
2. **Storage** → create public bucket `payment-screenshots`.
3. **Database** → copy **Session mode** connection URI → Render `DATABASE_URL`.

See [supabase-env-example.txt](../supabase-env-example.txt).

### 2. Render (API)

1. New Web Service → Docker → root `apps/api`.
2. Paste env from [render-env-example.txt](../render-env-example.txt).
3. Set `API_BASE_URL` to your Render URL after first deploy.
4. Health check path: `/health`.

### 3. Vercel (Web)

1. Root Directory: `apps/web`.
2. Paste env from [vercel-env-example.txt](../vercel-env-example.txt).
3. **Redeploy** after setting `NEXT_PUBLIC_API_URL`.

### 4. Smoke test

| Step | URL / action |
|------|----------------|
| API health | `GET https://<api>.onrender.com/health` |
| DB health | `GET https://<api>.onrender.com/health/db` |
| Events | `GET https://<api>.onrender.com/events` |
| Register (phone) | `https://hyderabadhangamaclub.vercel.app/register` |
| UPI + screenshot | Complete flow; confirm URL in DB is `https://*.supabase.co/storage/...` |
| Admin | Approve payment; screenshot visible |
| Scanner | Scan ticket QR |

---

## Environment file index

| File | Purpose |
|------|---------|
| [.env.example](../.env.example) | Index / pointers |
| [apps/api/.env.example](../apps/api/.env.example) | Local API |
| [apps/web/.env.example](../apps/web/.env.example) | Local web |
| [render-env-example.txt](../render-env-example.txt) | Render production |
| [vercel-env-example.txt](../vercel-env-example.txt) | Vercel production |
| [supabase-env-example.txt](../supabase-env-example.txt) | Supabase dashboard |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| API won't start on Render | Check Render logs for `Production configuration is incomplete` |
| CORS error in browser | Set `CORS_ORIGINS` to exact Vercel URL |
| Screenshot 503 | Set `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`; bucket must exist |
| Admin image broken | Bucket must be **public**; URL must start with `https://` |
| Vercel build fails | Set `NEXT_PUBLIC_API_URL` to HTTPS Render URL |
| DB connection fails | Use Session pooler URI; `DATABASE_SSL=true` for Supabase |
| Cold start slow | Render Free spins down — first request may take 30–60s |

---

## Related docs

- [DEPLOYMENT_PLAN.md](./DEPLOYMENT_PLAN.md) — architecture & risks
- [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) — ordered tasks
