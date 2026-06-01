# Hyderabad Hangama Club

> Production-ready event ticketing MVP
>
> [![CI](https://github.com/saisankar428/hyderabad-hangama-club/actions/workflows/ci.yml/badge.svg)](https://github.com/saisankar428/hyderabad-hangama-club/actions/workflows/ci.yml)
>
> ## Overview
>
> Full-stack event ticketing platform: Register, Pay via Razorpay, Get QR Ticket, delivered via Email + WhatsApp, scan at entrance.
>
> ## Tech Stack
>
> | Layer | Technology |
> |-------|-----------|
> | Frontend | Next.js 15, TypeScript, Tailwind CSS, Shadcn UI |
> | Forms | React Hook Form + Zod |
> | Backend | FastAPI, Python 3.12, SQLAlchemy 2.0 |
> | Database | PostgreSQL 16 |
> | Cache | Redis 7 |
> | Payments | Razorpay |
> | Email | SendGrid |
> | WhatsApp | Twilio |
> | Container | Docker + Docker Compose |
> | CI/CD | GitHub Actions |
>
> ## Repository Structure
>
> ```
> hyderabad-hangama-club/
> +-- apps/
> |   +-- web/              # Next.js 15 frontend
> |   |   +-- src/
> |   |   |   +-- app/      # App Router pages
> |   |   |   +-- features/ # Feature components
> |   |   |   +-- components/
> |   |   +-- Dockerfile
> |   |   +-- package.json
> |   |   +-- next.config.ts
> |   |   +-- tsconfig.json
> |   +-- api/              # FastAPI backend
> |       +-- src/
> |       |   +-- core/     # Config, DB
> |       |   +-- domain/   # SQLAlchemy models
> |       |   +-- features/ # Feature routers + services
> |       |   +-- infrastructure/ # Email, WhatsApp
> |       +-- tests/
> |       +-- Dockerfile
> |       +-- requirements.txt
> +-- docs/
> |   +-- SETUP.md
> |   +-- ARCHITECTURE.md
> |   +-- API.md
> |   +-- ENV.md
> +-- .github/
> |   +-- workflows/
> |       +-- ci.yml
> +-- docker-compose.yml
> +-- nginx.conf
> +-- .env.example
> +-- .gitignore
> ```
>
> ## Quick Start
>
> ```bash
> git clone https://github.com/saisankar428/hyderabad-hangama-club.git
> cd hyderabad-hangama-club
> cp .env.example apps/api/.env
> cp .env.example apps/web/.env.local
> docker-compose up --build
> ```
>
> - Frontend: http://localhost:3000
> - - API: http://localhost:8000
>   - - Swagger: http://localhost:8000/docs
>     - - Scanner: http://localhost:3000/scanner
>      
>       - ## User Flow
>      
>       - 1. User visits event page
>         2. 2. Fills name, email, phone
>            3. 3. Clicks Register & Pay (Razorpay opens)
>               4. 4. Completes payment
>                  5. 5. QR ticket generated instantly
>                     6. 6. Email with QR code sent (SendGrid)
>                        7. 7. WhatsApp message sent (Twilio)
>                           8. 8. At event: staff scans at /scanner
>                              9. 9. Entry granted/denied
>                                
>                                 10. ## Documentation
>                                
>                                 11. - [Setup Guide](docs/SETUP.md)
>                                     - - [Deployment (Vercel + public API)](docs/DEPLOYMENT.md)
>                                       - - [Architecture](docs/ARCHITECTURE.md)
>                                       - - [API Reference](docs/API.md)
>                                         - - [Environment Variables](docs/ENV.md)
>                                          
>                                           - ## License
>                                          
>                                           - MIT
