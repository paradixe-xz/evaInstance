"""Pydantic schemas for email integration."""
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field


class EmailSendRequest(BaseModel):
    """Request body for sending emails."""

    to: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, max_length=255)
    text: Optional[str] = Field(None, description="Plain text body")
    html: Optional[str] = Field(None, description="HTML body")
    reply_to: Optional[EmailStr] = Field(None, description="Reply-to email address")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EmailMessageData(BaseModel):
    """Persisted email message metadata."""

    message_id: int
    session_id: int
    user_id: int
    external_id: Optional[str] = None
    channel: str


class EmailSendResponse(BaseModel):
    """Response payload when sending emails."""

    status: str
    provider_response: Dict[str, Any]
    message: EmailMessageData


class EmailWebhookResponse(BaseModel):
    """Response payload sent back to Resend webhook acknowledgements."""

    status: str = Field(..., description="Processing status")
