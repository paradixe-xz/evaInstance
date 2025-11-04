"""Email service to interact with external Resend microservice."""
from typing import Any, Dict, Optional

import httpx

from ..core.config import get_settings
from ..core.exceptions import ServiceUnavailableError
from ..core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class EmailService:
    """Service for sending emails through the Resend microservice."""

    def __init__(self) -> None:
        self.base_url = settings.email_service_url.rstrip("/")
        # reuse generic timeout setting to avoid hardcoding another value
        self.timeout = settings.ollama_timeout or 30

    async def send_email(
        self,
        to: str,
        subject: str,
        text: str,
        html: Optional[str] = None,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send email via the Resend microservice."""

        payload = {
            "to": to,
            "subject": subject,
            "text": text,
            "html": html,
            "replyTo": reply_to,
            "metadata": metadata or {},
        }

        logger.info("Sending email via Resend microservice to %s", to)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/send-email",
                    json=payload,
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Email service responded with error %s: %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise ServiceUnavailableError(
                "Email service error",
                error_code="EMAIL_SERVICE_ERROR",
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Error connecting to email service: %s", str(exc))
            raise ServiceUnavailableError(
                "Email service unavailable",
                error_code="EMAIL_SERVICE_UNAVAILABLE",
            ) from exc
