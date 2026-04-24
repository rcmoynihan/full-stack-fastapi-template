# FastAPI Project - Backend

## Requirements

* [Docker](https://www.docker.com/).
* [uv](https://docs.astral.sh/uv/) for Python package and environment management.

## Docker Compose

Start the local development environment with Docker Compose following the guide in [../development.md](../development.md).

## General Workflow

By default, the dependencies are managed with [uv](https://docs.astral.sh/uv/), go there and install it.

From `./backend/` you can install all the dependencies with:

```console
$ uv sync
```

Then you can activate the virtual environment with:

```console
$ source .venv/bin/activate
```

Make sure your editor is using the correct Python virtual environment, with the interpreter at `backend/.venv/bin/python`.

Modify or add SQLModel models for data and SQL tables in `./backend/app/models.py`, API endpoints in `./backend/app/api/`, CRUD (Create, Read, Update, Delete) utils in `./backend/app/crud.py`.

## Local Development

Use the repository-level commands documented in [../development.md](../development.md).
For backend-only work, start local dependencies with Docker Compose and run the
FastAPI development server from the backend environment.

## Backend tests

To test the backend run:

```console
$ just backend-test
```

The tests run with Pytest, modify and add tests to `./backend/tests/`.

If you use GitHub Actions the tests will run automatically.

### Test running stack

If your stack is already up and you just want to run the tests, you can use:

```bash
docker compose exec backend bash scripts/tests-start.sh
```

That `/app/scripts/tests-start.sh` script forces local test database settings, waits for the local database, and then calls `pytest`. If you need to pass extra arguments to `pytest`, you can pass them to that command and they will be forwarded.

For example, to stop on first error:

```bash
docker compose exec backend bash scripts/tests-start.sh -x
```

### Test Coverage

When the tests are run, a file `htmlcov/index.html` is generated, you can open it in your browser to see the coverage of the tests.

## Migrations

Make sure you create a "revision" of your models and that you "upgrade" your database with that revision every time you change them. As this is what will update the tables in your database. Otherwise, your application will have errors.

The local Compose stack builds the backend image from your checked-out source.
Hot-reload development uses the optional `compose.watch.yml` overlay through
`just dev-watch`; the backend app directory is not mounted as a full source
volume by default.

For host-based development, create and apply migrations from the repository
root:

```console
$ just migrate-create "Add column last_name to User model"
$ just migrate
```

* Alembic is already configured to import your SQLModel models from `./backend/app/models.py`.

If you already have the backend container running and intentionally want to run
Alembic there, you can execute the same commands in the container:

```console
$ docker compose exec backend alembic revision --autogenerate -m "Add column last_name to User model"
$ docker compose exec backend alembic upgrade head
```

* Commit to the git repository the files generated in the alembic directory.

Migrations are required for deployed environments. The Fly backend
`release_command` runs `backend/scripts/migrate.sh`, which applies Alembic
migrations before new machines take traffic.
