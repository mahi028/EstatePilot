# EstatePilot

A property maintenance management system with role-based access for **Managers**, **Tenants**, and **Technicians**.

Managers invite tenants, oversee maintenance tickets, and assign technicians. Tenants create tickets for property issues once linked to a manager. Technicians handle assigned work orders.

## Tech Stack

- **Backend** — Flask, Flask-RESTful, SQLAlchemy, Flask-JWT-Extended, SQLite
- **Frontend** — Vue 3, Vue Router, Pinia, Tailwind CSS v4, Axios

## Prerequisites

- Python 3.12+
- Node.js 22.12+
- [uv](https://docs.astral.sh/uv/) (recommended for backend)

## Setup

### Backend

```bash
cd backend

# Create .env
cp .env.example .env   # or create manually (see below)

# Install dependencies & run
uv sync
uv run flask db upgrade   # apply migrations
uv run python main.py     # starts on http://localhost:5000
```

Minimal `.env`:

```
SECRET_KEY=your-secret-key
SQLALCHEMY_DATABASE_URI=sqlite:///database.sqlite3
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # starts on http://localhost:5173
```

Create `frontend/.env` if the backend runs on a non-default port:

```
VITE_API_URL=http://localhost:5000/api
```

## Running Tests

```bash
cd backend
uv run pytest
```