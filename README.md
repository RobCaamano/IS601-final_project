# Final Project

A FastAPI + PostgreSQL calculations app: users register, log in, and perform BREAD
(Browse, Read, Edit, Add, Delete) operations on calculations (addition, subtraction,
multiplication, division) through both a REST API and a server-rendered web UI.

## User Profile & Password Change

The final-project feature added on top of the base app is self-service account
management:

- `PUT /users/{user_id}` — update your own username and/or email.
- `PUT /users/{user_id}/password` — change your own password (requires the current
  password).
- An **Account Settings** page (`/account`), linked from the header once logged in,
  with separate forms for profile info and password changes.
- Both endpoints are covered by integration and end-to-end tests.

## Architecture

- **`app/main.py`** — the FastAPI app: all HTTP routes live here, both the JSON API
  (`/auth/*`, `/calculations/*`, `/users/*`) and the web routes that render HTML
  pages (`/`, `/login`, `/dashboard`, `/account`, etc.).
- **`app/models/`** — SQLAlchemy models (`User`, `Calculation`). `User` also owns
  auth-related behavior (password hashing/verification, token creation) as methods
  on the model.
- **`app/schemas/`** — Pydantic schemas that validate request bodies and shape
  responses (e.g. `UserCreate`, `UserUpdate`, `PasswordUpdate`, `CalculationBase`).
  Validation rules (password strength, matching confirmation fields, etc.) live here.
- **`app/auth/`** — JWT issuing/verification and the `get_current_active_user`
  dependency that protected routes use to identify the caller from the
  `Authorization: Bearer` header.
- **`app/database.py`** — SQLAlchemy engine/session setup. Tables are created on
  app startup using a lifespan hook.
- **`templates/` + `static/`** — Jinja2 templates (Tailwind) for the web UI.
  Pages are mostly static HTML shells; vanilla JS in each template's` calls the JSON API with `fetch`.
- **Postgres** runs as its own container (`docker-compose.yml`). the `web` service
  depends on it being healthy before starting.

## DockerHub Repo
[DockerHub Repo](https://hub.docker.com/repository/docker/robcaamano/601_final_project)

## How to run tests locally

### Prerequisites
- A Postgres instance matching `DATABASE_URL` (see `app/config.py`, default `postgresql://postgres:postgres@localhost:5432/fastapi_db`). The `db` service in `docker-compose.yml` provides this:
```
docker-compose up -d db
```
- Playwright browsers (needed for the UI test fixtures in `tests/conftest.py`):
```
playwright install --with-deps chromium
```

### Running tests
```
# Full test suite as defined in pytest.ini
pytest

# Specific file
pytest -s -v tests/<type>/<file>

# Keep data after tests (skip table truncation/drop)
pytest --preserve-db

# Include tests marked @pytest.mark.slow (skipped by default)
pytest --run-slow

# Run only a specific marker (slow / fast / e2e)
pytest -m e2e
```

Coverage is collected automatically (`pytest.ini` sets `--cov=app`); an HTML report is written to `htmlcov/index.html` after each run.

## How to run UI

### Prerequisites
- Docker must be running. On Windows/WSL, make sure Docker Desktop is open and its WSL integration is enabled before continuing (`docker info` should succeed without errors).

### Start the app
```
docker-compose up -d
```

### Access the UI
Open [http://localhost:8000](http://localhost:8000) in your browser.

## Reflection

The backend half of this feature was pretty straightforward — most of the pieces were already built in module 14 before I started. The `UserUpdate` and `PasswordUpdate` Pydantic
schemas already existed with their validation rules in place, the `User` model already had password hashing/verification and a generic `update()` helper, and the
`get_current_active_user` auth dependency was already used throughout the calculations routes. The main work was piecing those parts together into the two
new endpoints, adding the authorization check so users can only edit their own account, and writing tests for it.

The UI side took more effort for me. I work primarily on backend systems day to day, so building out the account settings page was less familiar territory than the API work. Leaning on the existing templates (`edit_calculation.html`, `register.html`) as a reference for how forms, alerts, and API calls were already being done in this codebase made it much easier to
keep the new page consistent with the rest of the app instead of reinventing those patterns.
