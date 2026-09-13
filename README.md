# Pingu Tools <img src="app/static/favicon.svg" width="32" height="32" align="left" alt="Pingu Tools logo">

Pingu Tools is a small set of self-hosted web utilities built with FastAPI. So far there's one tool, a URL shortener with user accounts. You sign up, shorten links, and manage them from a dashboard. [`TODO.md`](TODO.md) lists what's planned next.

## Current features

- Create, edit, and delete short links.
- User accounts with session-cookie auth and bcrypt-hashed passwords. Each user sees only their own links, and the server checks ownership before any edit or delete.
- Each user can keep up to 30 links. Change `MAX_URLS_PER_USER` in `app/main.py` to raise it.

## Tech stack

- [FastAPI](https://fastapi.tiangolo.com/) + [Jinja2](https://jinja.palletsprojects.com/) templates
- [SQLAlchemy](https://www.sqlalchemy.org/) + [Alembic](https://alembic.sqlalchemy.org/) migrations
- PostgreSQL, run locally in Docker
- [pytest](https://docs.pytest.org/) for tests

## Development setup

### Prerequisites

- Python 3.9+
- Docker, for the Postgres database

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

Open `.env` and set `SECRET_KEY` to a real value. The app signs session cookies with it. You can leave the Postgres values alone for local development.

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

Open [http://localhost:8000](http://localhost:8000).

## Running tests

The tests use a separate `url_shortener_test` database on the same Postgres instance, so your dev data stays untouched. Create it once:

```bash
docker exec url-shortener-postgres psql -U postgres -c "CREATE DATABASE url_shortener_test;"
```

Then run the suite:

```bash
pytest
```

CI runs the same suite on every push and pull request to `master`. The workflow lives in `.github/workflows/ci.yml`.

## Deployment

The app deploys to [Render](https://render.com) through the `render.yaml` Blueprint. Render builds the web service from the `Dockerfile`, creates a Postgres database, and passes the database credentials to the web service as environment variables.

1. Push this repo to GitHub.
2. In the Render dashboard, choose **New +** → **Blueprint** and connect the repo.
3. Render reads `render.yaml` and creates the `pingu-tools` web service and the `pingu-tools-db` database. It also generates `SECRET_KEY`, so you don't have to set any secrets by hand.
4. After the first deploy, every push to `master` triggers a new one. The container runs `alembic upgrade head` before starting uvicorn, so migrations apply on each deploy.

Both services are on Render's free plan, which has two catches. The web service sleeps after 15 minutes without traffic, and the next request takes 30 to 60 seconds to wake it. Worse, Render deletes the free Postgres database 30 days after you create it. That's fine for testing a deploy. If you want to keep your data, change `plan` for `pingu-tools-db` in `render.yaml` or the Render dashboard before day 30. You can upgrade `pingu-tools` too if the cold starts bother you.
