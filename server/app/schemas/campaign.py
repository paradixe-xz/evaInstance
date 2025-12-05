"""
Campaign schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CampaignBase(BaseModel):
    """Base campaign schema"""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    campaign_type: str = Field(default="mixed", pattern="^(calls|whatsapp|mixed)$")
    target_audience: Optional[str] = None
    goals: Optional[str] = None


class CampaignCreate(CampaignBase):
    """Campaign creation schema"""
    environment_variables: Optional[Dict[str, Any]] = None
    call_numbers: Optional[List[str]] = None
    whatsapp_numbers: Optional[List[str]] = None
    whatsapp_webhook_url: Optional[str] = None
    whatsapp_verify_token: Optional[str] = None
    whatsapp_access_token: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CampaignUpdate(BaseModel):
    """Campaign update schema"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|active|paused|completed)$")
    campaign_type: Optional[str] = Field(None, pattern="^(calls|whatsapp|mixed)$")
    target_audience: Optional[str] = None
    goals: Optional[str] = None
    environment_variables: Optional[Dict[str, Any]] = None
    call_numbers: Optional[List[str]] = None
    whatsapp_numbers: Optional[List[str]] = None
    whatsapp_webhook_url: Optional[str] = None
    whatsapp_verify_token: Optional[str] = None
    whatsapp_access_token: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class CampaignResponse(CampaignBase):
    """Campaign response schema"""
    id: int
    slug: str
    status: str
    is_active: bool
    environment_variables: Optional[Dict[str, Any]]
    call_numbers: Optional[List[str]]
    whatsapp_numbers: Optional[List[str]]
    whatsapp_webhook_url: Optional[str]
    total_calls: int
    successful_calls: int
    total_whatsapp_messages: int
    total_conversations: int
    success_rate: float
    avg_call_duration: float
    avg_response_time: float
    total_cost: float
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignMetrics(BaseModel):
    """Campaign metrics schema"""
    total_calls: int
    successful_calls: int
    total_whatsapp_messages: int
    total_conversations: int
    success_rate: float
    avg_call_duration: float
    avg_response_time: float
    total_cost: float


class CampaignSummary(BaseModel):
    """Campaign summary schema"""
    id: int
    name: str
    slug: str
    status: str
    campaign_type: str
    success_rate: float
    total_calls: int
    total_whatsapp_messages: int
    created_at: datetime

    class Config:
        from_attributes = True