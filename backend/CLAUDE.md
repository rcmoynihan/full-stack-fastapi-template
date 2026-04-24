# Backend CLAUDE.md

## Setup
- Python 3.14, managed by uv
- `uv sync` to install dependencies
- `uv run fastapi dev app/main.py` for local dev server

## Configuration
- Pydantic Settings in `app/core/config.py`
- Local dev reads the repo `.env` file
- Deployed environments should use environment variables and managed secrets
- Key settings: DATABASE_URL or POSTGRES_* values, SECRET_KEY, FIRST_SUPERUSER

## Database
- SQLModel with SQLAlchemy underneath
- Alembic migrations in `app/alembic/versions/`
- Models in `app/models.py`, CRUD in `app/crud.py`
- Engine created in `app/core/db.py`
- Migration policy: expand/contract only; no breaking schema changes in the same deploy as code that depends on them

## Adding a New Endpoint
1. Add or modify models in `app/models.py`
2. Add CRUD functions in `app/crud.py`
3. Create route in `app/api/routes/`
4. Register route in `app/api/main.py`
5. Create migration: `just migrate-create "description"`
6. Add tests in `tests/api/routes/`
7. Regenerate client: `just generate-client`
8. Run quality gate: `just check`

## Testing
- `just backend-test` runs all tests with coverage
- Tests hit a real Postgres instance from Docker Compose or local setup
- Coverage must be at least 92%
