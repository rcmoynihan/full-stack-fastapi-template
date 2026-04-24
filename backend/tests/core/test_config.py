from app.core.config import Settings


def test_database_url_is_normalized_for_deployments() -> None:
    """Production settings should prefer DATABASE_URL and enforce SSL."""
    app_settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        SUPABASE_PUBLISHABLE_KEY="sb_publishable_test",
        SUPABASE_SECRET_KEY="test-supabase-secret",
        FIRST_SUPERUSER="admin@example.com",
        FIRST_SUPERUSER_PASSWORD="not-a-default-password",
        DATABASE_URL="postgres://user:pass@example.com:5432/app",
    )

    assert str(app_settings.SQLALCHEMY_DATABASE_URI) == (
        "postgresql+psycopg://user:pass@example.com:5432/app?sslmode=require"
    )


def test_migrations_prefer_direct_database_url() -> None:
    """Alembic settings should use DATABASE_URL_DIRECT when configured."""
    app_settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        SUPABASE_PUBLISHABLE_KEY="sb_publishable_test",
        SUPABASE_SECRET_KEY="test-supabase-secret",
        FIRST_SUPERUSER="admin@example.com",
        FIRST_SUPERUSER_PASSWORD="not-a-default-password",
        DATABASE_URL="postgresql+psycopg://user:pass@pooler.example.com:5432/app",
        DATABASE_URL_DIRECT=(
            "postgresql+psycopg://migration:pass@db.example.com:5432/app"
        ),
    )

    assert str(app_settings.SQLALCHEMY_MIGRATION_DATABASE_URI) == (
        "postgresql+psycopg://migration:pass@db.example.com:5432/app?sslmode=require"
    )


def test_local_settings_fall_back_to_postgres_components() -> None:
    """Local settings should build the database URL from component fields."""
    app_settings = Settings(
        _env_file=None,
        FIRST_SUPERUSER="admin@example.com",
        FIRST_SUPERUSER_PASSWORD="changethis",
        DATABASE_URL=None,
        DATABASE_URL_DIRECT=None,
        POSTGRES_SERVER="db",
        POSTGRES_PORT=5432,
        POSTGRES_DB="app",
        POSTGRES_USER="postgres",
        POSTGRES_PASSWORD="changethis",
    )

    assert str(app_settings.SQLALCHEMY_DATABASE_URI) == (
        "postgresql+psycopg://postgres:changethis@db:5432/app"
    )
