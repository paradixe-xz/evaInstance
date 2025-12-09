"""
Pydantic schemas for Chat API
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ChatHistoryRequest(BaseModel):
    """Schema for chat history request"""
    phone_number: str = Field(..., description="User phone number")
    limit: int = Field(default=50, ge=1, le=100, description="Number of messages to retrieve")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    
    @validator("phone_number")
    def validate_phone_number(cls, v):
        clean_number = "".join(filter(str.isdigit, v))
        if len(clean_number) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        return v


class UserInfo(BaseModel):
    """Schema for user information"""
    id: int
    phone_number: str
    name: str
    is_active: bool
    ai_paused: bool = False
    total_messages: int
    last_activity: Optional[str] = None


class MessageInfo(BaseModel):
    """Schema for message information"""
    id: int
    direction: str
    content: str
    message_type: str
    created_at: str
    timestamp: Optional[str] = None
    sent_at: Optional[str] = None
    received_at: Optional[str] = None
    is_read: bool
    is_delivered: bool


class ChatHistoryResponse(BaseModel):
    """Schema for chat history response"""
    user: Optional[UserInfo]
    messages: List[MessageInfo]
    total: int
    limit: int
    offset: int


class ActiveSessionUser(BaseModel):
    """Schema for active session user info"""
    id: int
    phone_number: str
    name: str


class ActiveSession(BaseModel):
    """Schema for active session"""
    session_id: int
    user: ActiveSessionUser
    started_at: Optional[str] = None
    last_message_at: Optional[str] = None
    message_count: int
    status: str


class ActiveSessionsResponse(BaseModel):
    """Schema for active sessions response"""
    sessions: List[ActiveSession]
    total: int


class ChatStatsResponse(BaseModel):
    """Schema for chat statistics"""
    total_users: int
    active_users: int
    total_sessions: int
    active_sessions: int
    total_messages: int
    messages_today: int
    avg_response_time: Optional[float] = None


class UserStatsRequest(BaseModel):
    """Schema for user statistics request"""
    phone_number: str = Field(..., description="User phone number")
    
    @validator("phone_number")
    def validate_phone_number(cls, v):
        clean_number = "".join(filter(str.isdigit, v))
        if len(clean_number) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        return v


class UserStatsResponse(BaseModel):
    """Schema for user statistics response"""
    user: UserInfo
    total_sessions: int
    active_sessions: int
    total_messages: int
    incoming_messages: int
    outgoing_messages: int
    avg_session_duration: Optional[float] = None
    last_session_at: Optional[str] = None


class BulkMessageRequest(BaseModel):
    """Schema for bulk message sending"""
    phone_numbers: List[str] = Field(..., min_items=1, max_items=100, description="List of phone numbers")
    message: str = Field(..., min_length=1, max_length=4096, description="Message content")
    
    @validator("phone_numbers")
    def validate_phone_numbers(cls, v):
        for phone in v:
            clean_number = "".join(filter(str.isdigit, phone))
            if len(clean_number) < 10:
                raise ValueError(f"Invalid phone number: {phone}")
        return v


class BulkMessageResponse(BaseModel):
    """Schema for bulk message response"""
    total_sent: int
    successful: List[str]
    failed: List[Dict[str, str]]
    errors: List[str]