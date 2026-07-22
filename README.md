<img src="app/static/favicon.svg" width="32" height="32" align="left" alt="Pingu Tools logo">

# Pingu Tools

Pingu Tools is a small, growing toolbox of self-hosted web utilities, built with FastAPI. The first tool is a **URL shortener** with per-user accounts — sign up, shorten links, and manage them from a dashboard. More tools are planned; see [`TODO.md`](TODO.md) for what's next.

## Current features

- URL shortener — create, edit, and delete short links
- Per-user accounts — session-cookie auth with bcrypt-hashed passwords; links are scoped and ownership-checked per user
- Per-user link limit

## Tech stack

- [FastAPI](https://fastapi.tiangolo.com/) + [Jinja2](https://jinja.palletsprojects.com/) templates
- [SQLAlchemy](https://www.sqlalchemy.org/) + [Alembic](https://alembic.sqlalchemy.org/) migrations
- PostgreSQL (via Docker)
- [pytest](https://docs.pytest.org/) for tests

## Development setup

### Prerequisites

- Python 3.9+
- Docker (for the Postgres database)

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd url-shortener
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # macOS/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set a real `SECRET_KEY` (used to sign session cookies). The Postgres values can be left as-is for local development.

### 4. Start Postgres

```bash
docker compose up -d
```

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Run the dev server

```bash
uvicorn app.main:app --reload
```

The app will be running at [http://localhost:8000](http://localhost:8000).

## Running tests

Tests run against a separate `url_shortener_test` database on the same Postgres instance, so they never touch your dev data. Create it once:

```bash
docker exec url-shortener-postgres psql -U postgres -c "CREATE DATABASE url_shortener_test;"
```

Then run the suite:

```bash
pytest
```

CI runs this same suite automatically on every push and pull request to `master` (see `.github/workflows/ci.yml`).

## Deployment

The app deploys to [Render](https://render.com) via the included `render.yaml` Blueprint, which provisions both the web service (built from the `Dockerfile`) and a managed Postgres database, and wires the connection details between them automatically.

1. Push this repo to GitHub.
2. In the Render dashboard, choose **New +** → **Blueprint**, and connect the repo.
3. Render reads `render.yaml` and creates the `pingu-tools` web service and `pingu-tools-db` database. `SECRET_KEY` is auto-generated; no manual secrets setup needed.
4. Once deployed, the service auto-deploys on every push to `master` — migrations run automatically on container start (see the `Dockerfile` `CMD`).

**Free tier caveats:** the free web service spins down after 15 minutes of inactivity (30-60s cold start on the next request), and the free Postgres database is auto-deleted 30 days after creation. Fine for getting a live URL up to test the deploy, but to keep it running long-term, upgrade the `plan` field for `pingu-tools-db` (and optionally `pingu-tools`) in `render.yaml` or directly in the Render dashboard before the 30-day mark.
