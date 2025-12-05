"""
Pydantic schemas for SIP Trunk management
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class SIPTrunkBase(BaseModel):
    """Base schema for SIP Trunk"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    sip_username: str = Field(..., min_length=1, max_length=100)
    sip_password: str = Field(..., min_length=1)
    sip_domain: str = Field(..., min_length=1, max_length=255)
    sip_port: int = Field(default=5060, ge=1, le=65535)
    sip_transport: str = Field(default="UDP", pattern="^(UDP|TCP|TLS)$")
    remote_ip: Optional[str] = None
    local_ip: Optional[str] = None
    local_port: Optional[int] = Field(None, ge=1, le=65535)
    max_concurrent_calls: int = Field(default=10, ge=1, le=1000)
    require_authentication: bool = Field(default=True)
    auth_username: Optional[str] = None
    auth_realm: Optional[str] = None
    ip_whitelist: Optional[List[str]] = None
    inbound_routing: Optional[Dict[str, Any]] = None
    outbound_routing: Optional[Dict[str, Any]] = None
    allowed_prefixes: Optional[List[str]] = None
    blocked_prefixes: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class SIPTrunkCreate(SIPTrunkBase):
    """Schema for creating a SIP Trunk"""
    pass


class SIPTrunkUpdate(BaseModel):
    """Schema for updating a SIP Trunk"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    sip_password: Optional[str] = None
    sip_domain: Optional[str] = Field(None, min_length=1, max_length=255)
    sip_port: Optional[int] = Field(None, ge=1, le=65535)
    sip_transport: Optional[str] = Field(None, pattern="^(UDP|TCP|TLS)$")
    remote_ip: Optional[str] = None
    local_ip: Optional[str] = None
    local_port: Optional[int] = Field(None, ge=1, le=65535)
    is_active: Optional[bool] = None
    max_concurrent_calls: Optional[int] = Field(None, ge=1, le=1000)
    require_authentication: Optional[bool] = None
    auth_username: Optional[str] = None
    auth_realm: Optional[str] = None
    ip_whitelist: Optional[List[str]] = None
    inbound_routing: Optional[Dict[str, Any]] = None
    outbound_routing: Optional[Dict[str, Any]] = None
    allowed_prefixes: Optional[List[str]] = None
    blocked_prefixes: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class SIPTrunkResponse(BaseModel):
    """Schema for SIP Trunk response (excludes password)"""
    id: int
    name: str
    description: Optional[str] = None
    sip_username: str
    sip_domain: str
    sip_port: int
    sip_transport: str
    remote_ip: Optional[str] = None
    local_ip: Optional[str] = None
    local_port: Optional[int] = None
    is_active: bool
    is_registered: bool
    registration_status: Optional[str]
    max_concurrent_calls: int
    current_calls: int
    total_calls: int
    successful_calls: int
    failed_calls: int
    last_call_at: Optional[datetime]
    last_registration_at: Optional[datetime]
    require_authentication: bool
    auth_username: Optional[str] = None
    auth_realm: Optional[str] = None
    ip_whitelist: Optional[List[str]] = None
    inbound_routing: Optional[Dict[str, Any]] = None
    outbound_routing: Optional[Dict[str, Any]] = None
    allowed_prefixes: Optional[List[str]] = None
    blocked_prefixes: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SIPTrunkListResponse(BaseModel):
    """Schema for listing SIP Trunks"""
    trunks: List[SIPTrunkResponse]
    total: int


class SIPTrunkRegisterRequest(BaseModel):
    """Schema for registering a SIP Trunk"""
    trunk_id: int


class SIPTrunkRegisterResponse(BaseModel):
    """Schema for SIP Trunk registration response"""
    success: bool
    message: str
    registration_status: Optional[str] = None


class SIPCallRequest(BaseModel):
    """Schema for initiating a SIP call"""
    trunk_id: int
    destination: str = Field(..., min_length=1, max_length=50)
    caller_id: Optional[str] = None
    timeout: Optional[int] = Field(default=30, ge=5, le=300)


class SIPCallResponse(BaseModel):
    """Schema for SIP call response"""
    success: bool
    call_id: Optional[str] = None
    message: str
    status: Optional[str] = None

