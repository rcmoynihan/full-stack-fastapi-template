import uuid
import warnings
from typing import Annotated, Any, Literal, Self

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    """Parse CORS origins from a comma-delimited string or list.

    Args:
        v: Raw CORS value loaded from settings.

    Returns:
        Parsed origins for Pydantic validation.
    """
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    """Application settings loaded from environment variables and local `.env`.

    Local development may use the repository `.env` file. Staging and production
    should provide settings through environment variables or platform secrets.
    """

    model_config = SettingsConfigDict(
        # .env is for local development only. Deployed environments use env vars.
        env_file=("../.env", "../.env.supabase.local"),
        env_ignore_empty=True,
        extra="ignore",
    )
    API_V1_STR: str = "/api/v1"
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str = "Full Stack FastAPI Project"
    SENTRY_DSN: HttpUrl | None = None

    SUPABASE_URL: str = "http://127.0.0.1:55321"
    SUPABASE_AUTH_URL: str | None = None
    SUPABASE_PUBLISHABLE_KEY: str = ""
    SUPABASE_SECRET_KEY: str = ""
    SUPABASE_JWT_SECRET: str | None = None
    SUPABASE_JWT_AUDIENCE: str = "authenticated"
    SUPABASE_JWT_ISSUER: str | None = None

    DATABASE_URL: str | None = None
    DATABASE_URL_DIRECT: str | None = None

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "app"

    WEB_CONCURRENCY: int = 1
    SQLALCHEMY_POOL_SIZE: int = 2
    SQLALCHEMY_MAX_OVERFLOW: int = 0
    SQLALCHEMY_POOL_TIMEOUT: int = 30

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn | str:
        """Database URL used by the application.

        Returns:
            A PostgreSQL URL, preferring DATABASE_URL over component settings.
        """
        if self.DATABASE_URL:
            return self._normalize_postgres_url(self.DATABASE_URL)

        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    @property
    def SQLALCHEMY_MIGRATION_DATABASE_URI(self) -> PostgresDsn | str:
        """Database URL used by Alembic migrations.

        Returns:
            A direct PostgreSQL URL when DATABASE_URL_DIRECT is configured,
            otherwise the application database URL.
        """
        if self.DATABASE_URL_DIRECT:
            return self._normalize_postgres_url(self.DATABASE_URL_DIRECT)
        return self.SQLALCHEMY_DATABASE_URI

    def _normalize_postgres_url(self, raw_url: str) -> str:
        """Normalize managed Postgres URLs for SQLAlchemy and SSL.

        Args:
            raw_url: Raw PostgreSQL connection URL.

        Returns:
            URL with the psycopg driver prefix and required SSL for deployments.
        """
        url = raw_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://") and "+psycopg" not in url:
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)

        if self.ENVIRONMENT != "local" and "sslmode=" not in url.lower():
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}sslmode=require"

        return url

    EMAIL_TEST_USER: EmailStr = "test@example.com"
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_ID: uuid.UUID = uuid.UUID("00000000-0000-4000-8000-000000000001")
    FIRST_SUPERUSER_PASSWORD: str

    GIT_SHA: str = "unknown"

    @property
    def supabase_auth_base_url(self) -> str:
        """Return the backend-reachable Supabase Auth API base URL.

        Returns:
            Supabase URL without a trailing slash.
        """
        return (self.SUPABASE_AUTH_URL or self.SUPABASE_URL).rstrip("/")

    @property
    def supabase_jwks_url(self) -> str:
        """Return the Supabase Auth JWKS endpoint URL.

        Returns:
            Fully-qualified JWKS URL for JWT signature verification.
        """
        return f"{self.supabase_auth_base_url}/auth/v1/.well-known/jwks.json"

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        """Warn locally and fail deployments when a secret is missing/default.

        Args:
            var_name: Setting name used in the diagnostic message.
            value: Secret value to validate.
        """
        if not value or value in {"changethis", "changethis-dev-only"}:
            message = (
                f"The value of {var_name} is missing or set to a development default; "
                "for security, set a real value for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        """Validate deployment-only security requirements.

        Returns:
            Validated settings instance.
        """
        if not self.DATABASE_URL:
            self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret("SUPABASE_SECRET_KEY", self.SUPABASE_SECRET_KEY)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )
        if self.ENVIRONMENT != "local" and not self.DATABASE_URL:
            raise ValueError("DATABASE_URL must be set in staging/production.")
        if self.ENVIRONMENT != "local" and not self.SUPABASE_PUBLISHABLE_KEY:
            raise ValueError("SUPABASE_PUBLISHABLE_KEY must be set in deployments.")

        return self


settings = Settings()  # type: ignore
