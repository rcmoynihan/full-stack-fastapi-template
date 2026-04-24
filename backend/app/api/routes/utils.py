import structlog
from fastapi import APIRouter, HTTPException, status
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import engine
from app.models import HealthCheck

router = APIRouter(prefix="/utils", tags=["utils"])
logger = structlog.get_logger(__name__)


@router.get("/health-check/")
def health_check() -> HealthCheck:
    """Check application health and database connectivity.

    Returns:
        Health status with deployment metadata.

    Raises:
        HTTPException: Raised with 503 when the database check fails.
    """
    try:
        with Session(engine) as session:
            session.exec(select(1))
    except Exception as exc:
        logger.warning("health_check_database_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connectivity check failed.",
        ) from exc

    return HealthCheck(
        status="ok",
        database="ok",
        git_sha=settings.GIT_SHA,
        environment=settings.ENVIRONMENT,
    )
