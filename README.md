# EstatePilot

EstatePilot is a role-based property maintenance platform for managers, tenants, and technicians.

- Tenants create maintenance tickets (with optional images at creation time) and track progress.
- Managers manage tenant workflows, review tickets, and assign/request technicians.
- Technicians work from two focused queues:
	- My Tickets: assigned and active requests
	- Service Area Opportunities: open jobs in their service area

## Tech Stack

- Backend: Flask, Flask-RESTful, SQLAlchemy, Flask-JWT-Extended, SQLite
- Frontend: Vue 3, Vue Router, Pinia, Tailwind CSS v4, Axios, Vite

## Prerequisites

- Python 3.12+
- Node.js 22.12+ (project enforces `^20.19.0 || >=22.12.0`)
- uv: https://docs.astral.sh/uv/
- Docker + Docker Compose (optional, for containerized run)

## Local Development

### 1) Backend

```bash
cd backend

# Create env file
cp .env.example .env

# Install and migrate
uv sync
uv run flask --app main db upgrade

# Run API
uv run python main.py
```

Backend URL: http://localhost:5000

Minimal backend `.env`:

```env
SECRET_KEY=your-secret-key
SQLALCHEMY_DATABASE_URI=sqlite:///database.sqlite3
```

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: http://localhost:5173

If backend is not on default URL, create `frontend/.env`:

```env
VITE_API_URL=http://localhost:5000/api
```

## Docker (Recommended)

From repo root:

```bash
docker compose up --build -d
```

App URL: http://localhost:8080

Stop services:

```bash
docker compose down
```

Notes:

- Caddy proxies frontend and backend through port 8080.
- SQLite data and uploads are persisted in Docker volumes (`backend_data`, `backend_uploads`).

## Useful Commands

Backend tests:

```bash
cd backend
uv run pytest
```

Frontend production build:

```bash
cd frontend
npm run build
```

## Core Workflows

- Manager invitation flow: managers invite tenants, tenants accept/reject.
- Ticket lifecycle: open -> assigned -> in_progress -> done/invalid.
- Tenant ticket creation supports image uploads in the initial create form.
- Technician routing separates service-area opportunities from assigned work for cleaner navigation.