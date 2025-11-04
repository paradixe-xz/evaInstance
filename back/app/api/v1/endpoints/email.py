"""Email API endpoints for Resend integration."""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from ....core.logging import get_logger
from ....core.exceptions import ServiceUnavailableError
from ....services.email_service import EmailService
from ....services.email_chat_service import EmailChatService
from ....schemas.email import EmailSendRequest, EmailSendResponse, EmailWebhookResponse

logger = get_logger(__name__)
router = APIRouter()

email_service = EmailService()
email_chat_service = EmailChatService()


@router.post("/send", response_model=EmailSendResponse)
async def send_email(request: EmailSendRequest) -> EmailSendResponse:
    """Send an outbound email via Resend microservice."""
    try:
        logger.info("Sending email to %s", request.to)
        result = await email_service.send_email(
            to=request.to,
            subject=request.subject,
            text=request.text or "",
            html=request.html,
            reply_to=request.reply_to,
            metadata=request.metadata,
        )

        message_data = email_chat_service.persist_outgoing_email(request, result)

        return EmailSendResponse(
            status="sent",
            provider_response=result,
            message=message_data,
        )
    except ServiceUnavailableError as exc:
        logger.error("Email service unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="Email service unavailable") from exc
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Failed to send email")
        raise HTTPException(status_code=500, detail="Failed to send email") from exc


@router.post("/webhook", response_model=EmailWebhookResponse)
async def email_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> EmailWebhookResponse:
    """Handle inbound email webhook events from Resend."""
    try:
        payload = await request.json()
        logger.info("Received email webhook payload")

        background_tasks.add_task(email_chat_service.process_incoming_email, payload)

        return EmailWebhookResponse(status="queued")
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Email webhook processing failed")
        raise HTTPException(status_code=500, detail="Failed to process email webhook") from exc
