"""
Pydantic schemas for WhatsApp API
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator


class WebhookVerification(BaseModel):
    """Schema for webhook verification"""
    hub_mode: str = Field(..., alias="hub.mode")
    hub_verify_token: str = Field(..., alias="hub.verify_token")
    hub_challenge: str = Field(..., alias="hub.challenge")


class SendMessageRequest(BaseModel):
    """Schema for sending messages"""
    phone_number: str = Field(..., description="Recipient phone number")
    message: str = Field(..., min_length=1, max_length=4096, description="Message content")
    
    @validator("phone_number")
    def validate_phone_number(cls, v):
        # Remove all non-digit characters
        clean_number = "".join(filter(str.isdigit, v))
        if len(clean_number) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        return v


class SendMessageResponse(BaseModel):
    """Schema for send message response"""
    status: str
    user_id: int
    session_id: int
    message_id: int
    whatsapp_response: Dict[str, Any]


class WebhookMessage(BaseModel):
    """Schema for incoming webhook messages"""
    object: str
    entry: List[Dict[str, Any]]


class MessageProcessingResponse(BaseModel):
    """Schema for message processing response"""
    status: str
    user_id: Optional[int] = None
    session_id: Optional[int] = None
    incoming_message_id: Optional[int] = None
    outgoing_message_id: Optional[int] = None
    ai_response: Optional[str] = None
    error: Optional[str] = None
    note: Optional[str] = None


class TemplateMessageRequest(BaseModel):
    """Schema for sending template messages"""
    phone_number: str = Field(..., description="Recipient phone number")
    template_name: str = Field(..., description="Template name")
    language_code: str = Field(default="es", description="Language code")
    parameters: Optional[List[str]] = Field(default=None, description="Template parameters")
    
    @validator("phone_number")
    def validate_phone_number(cls, v):
        clean_number = "".join(filter(str.isdigit, v))
        if len(clean_number) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        return v