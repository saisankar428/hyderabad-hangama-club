# Setup Guide - Hyderabad Hangama Club

## Prerequisites

- Docker Desktop 4.x+
- - Node.js 20+
  - - Python 3.12+
    - - Git
     
      - ## Quick Start (Docker)
     
      - ```bash
        git clone https://github.com/saisankar428/hyderabad-hangama-club.git
        cd hyderabad-hangama-club
        cp .env.example apps/api/.env
        cp .env.example apps/web/.env.local
        docker-compose up --build
        ```

        Access:
        - Frontend: http://localhost:3000
        - - API: http://localhost:8000
          - - API Docs: http://localhost:8000/docs
           
            - ## Local Development
           
            - ### Backend (FastAPI)
           
            - ```bash
              cd apps/api
              python -m venv .venv
              source .venv/bin/activate  # Windows: .venv\Scripts\activate
              pip install -r requirements.txt
              cp .env.example .env
              # Edit .env with your credentials
              uvicorn src.main:app --reload --port 8000
              ```

              ### Frontend (Next.js)

              ```bash
              cd apps/web
              npm install
              cp .env.example .env.local
              # Edit .env.local with your credentials
              npm run dev
              ```

              ## Database Migrations

              ```bash
              cd apps/api
              alembic upgrade head
              alembic revision --autogenerate -m "description"
              ```

              ## Running Tests

              ```bash
              # API tests
              cd apps/api
              pytest tests/ -v --cov=src

              # Web tests
              cd apps/web
              npm run test
              npm run type-check
              ```

              ## Required External Services

              | Service | Purpose | Setup |
              |---------|---------|-------|
              | Razorpay | Payments | https://dashboard.razorpay.com |
              | SendGrid | Email | https://app.sendgrid.com |
              | Twilio | WhatsApp | https://console.twilio.com |
              | PostgreSQL | Database | Included in docker-compose |

              ## Production Deployment

              Use **[DEPLOYMENT.md](DEPLOYMENT.md)** for the full checklist (Vercel frontend + public API URL, CORS, PostgreSQL, etc.).

              Quick summary:

              1. Deploy API with PostgreSQL (Render/Railway/etc.)
              2. Set `API_BASE_URL`, `CORS_ORIGINS`, `ADMIN_DASHBOARD_URL` on the API
              3. Deploy web to Vercel with `NEXT_PUBLIC_API_URL` pointing at the API
              4. See [ENV.md](ENV.md) for all variables
