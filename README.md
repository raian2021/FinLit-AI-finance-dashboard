# FinLit (MVP) — Personal Finance Dashboard + AI Insights

FinLit is a local-first personal finance dashboard that imports **Monzo** and **Starling** transaction CSV exports, computes **cashflow + category breakdowns**, and generates **AI-powered educational insights** (not financial advice).

This MVP is built as a full-stack app:

- **Frontend:** Next.js (App Router) + Tailwind (+ optional shadcn/ui components)
- **Backend:** FastAPI + SQLAlchemy
- **Database:** Postgres
- **AI:** Anthropic (Claude) or OpenAI (optional fallback)

> ⚠️ **Education, not advice**: FinLit provides budgeting and educational insights only. It is not regulated financial advice.

---

## Features (Current MVP)

### Dashboard

- Total transaction count
- Date range (earliest/latest)
- "Where your money goes" breakdown:
  - Essentials / Discretionary / Savings & Investments
  - Top discretionary categories
  - Monthly deficit indicator (when applicable)

### CSV Import (Monzo & Starling)

- Upload CSV from UI
- Server-side parsing + normalisation
- Duplicate detection (by bank + transaction id)
- Stores transactions in Postgres

### What-If Simulator

- Simple compounding model for redirecting monthly spend into investing
- Adjustable:
  - Monthly amount
  - Time horizon
  - Assumed annual return

### AI Financial Education (Optional)

- Generates an educational summary based on **aggregated** stats
- Does **not** require sending raw transaction rows (design intent)

---

## Tech Stack

| Layer        | Technology                          |
| ------------ | ----------------------------------- |
| **Frontend** | Next.js, Tailwind CSS, shadcn/ui    |
| **Backend**  | FastAPI, SQLAlchemy, Pydantic       |
| **Database** | PostgreSQL (Docker)                 |
| **AI**       | Anthropic Claude (default), OpenAI (fallback) |

---

## Repository Structure

```text
finlit/
  backend/                 # FastAPI backend
    app/
      api/                 # API routes
      core/                # settings, ai client, utils
      models/              # SQLAlchemy models
      parsers/             # CSV parsing + mapping
      schemas/             # Pydantic schemas
      services/            # import + aggregation logic
    migrations/            # Alembic migrations (if/when used)
    tests/
    Dockerfile
    requirements.txt

  frontend/                # Next.js frontend
    src/
      app/                 # Next.js routes (App Router)
      components/          # UI components (cards, shell)
      lib/                 # API client, helpers, utils
    Dockerfile
    tailwind.config.js
    package.json

  data/sample/             # Sample CSVs for testing
  scripts/                 # Utilities (e.g. sample data generator)

  docker-compose.yml
  Makefile
  .env.example
  .env
  README.md
```

---

## Quick Start (Docker)

### 1. Prerequisites

- Docker Desktop
- (Optional) Node + Python locally (not required if using Docker)

### 2. Configure environment

Copy the template:

```bash
cp .env.example .env
```

Update `.env` values (see [Environment Variables](#environment-variables) below).

### 3. Run the stack

From the repo root:

```bash
docker compose up --build
```

### 4. Open the app

- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **Backend API docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Environment Variables

Your `.env` controls DB, API auth, and AI provider.

### Database

These are set for Docker Compose networking (usually fine as-is):

- `DATABASE_URL`
- `DATABASE_URL_SYNC`

### API Security

Used to secure API requests from the frontend:

- `API_KEY` — value the frontend sends
- `SECRET_KEY` — used for signing / internal security primitives (if enabled)

> **Important:** Treat these like secrets. Don't commit `.env`.

### AI Provider

Choose one:

- `AI_PROVIDER=claude` (default) or `AI_PROVIDER=openai`

**Anthropic (Claude):**

- `ANTHROPIC_API_KEY=...`
- `ANTHROPIC_MODEL=...`

**OpenAI (fallback):**

- `OPENAI_API_KEY=...`
- `OPENAI_MODEL=...`

---

## Using Sample Data

This repo includes:

- `data/sample/monzo_sample.csv`
- `data/sample/starling_sample.csv`

You can upload them via the UI to populate the database.

If you have a generator script, run it from repo root:

```bash
python scripts/generate_sample_data.py
```

---

## API Authentication Notes

If you see `401 Unauthorized` in backend logs when the frontend loads stats, it means:

1. The frontend is not sending the expected API key header, or
2. `.env` values aren't aligned between services

**Typical fix:**

1. Ensure `.env` is present and values are correct
2. Restart stack:

```bash
docker compose down
docker compose up --build
```

---

## Common Dev Commands

**Stop:**

```bash
docker compose down
```

**Rebuild from scratch (after dependency changes):**

```bash
docker compose down
docker compose up --build
```

**View logs:**

```bash
docker compose logs -f
```

**Exec into containers:**

```bash
docker compose exec backend bash
docker compose exec frontend sh
docker compose exec db sh
```

---

## Roadmap (Next)

### UI/UX (first)

- Proper app layout (responsive sidebar / top-nav)
- Consistent typography and spacing system
- Better cards, charts, and loading states
- Transactions table + filters (date, category, merchant)
- "AI Insights" view with history + regenerate

### Security & Accounts

- Auth (local login) + session management
- Per-user data isolation
- Rate limiting + request validation
- Safer secret handling (env + vault later)

### Data & Analytics

- Stronger categorisation rules + overrides
- Budget targets and alerts
- Monthly reports + export
- Multi-account support

### AI Improvements

- Explainable insights
- Interactive "what changed this month" + follow-up Q&A
- Guardrails + deterministic fallbacks when AI unavailable

---

## Disclaimer

FinLit is an educational tool. It is not financial advice, and it does not provide regulated investment recommendations. Always do your own research or consult a qualified professional for financial advice.

---

## License

TBD (choose MIT/Apache-2.0 if open sourcing).