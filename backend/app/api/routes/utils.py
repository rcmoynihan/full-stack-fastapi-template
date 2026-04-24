import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic.networks import EmailStr
from sqlmodel import Session, select

from app.api.deps import get_current_active_superuser
from app.core.config import settings
from app.core.db import engine
from app.models import HealthCheck, Message
from app.utils import generate_test_email, send_email

router = APIRouter(prefix="/utils", tags=["utils"])
logger = structlog.get_logger(__name__)


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """Send a test email to the supplied address.

    Args:
        email_to: Recipient email address.

    Returns:
        Message confirming the email was sent.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


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
