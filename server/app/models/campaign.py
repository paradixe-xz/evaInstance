"""
Campaign model for Eva campaigns
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship

from ..core.database import Base


class Campaign(Base):
    """Campaign model for Eva campaigns"""
    
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    
    # Campaign status
    status = Column(String(20), default="draft")  # draft, active, paused, completed
    is_active = Column(Boolean, default=True)
    
    # Campaign configuration
    campaign_type = Column(String(50), default="mixed")  # calls, whatsapp, mixed
    target_audience = Column(Text, nullable=True)
    goals = Column(Text, nullable=True)
    
    # Environment variables for this campaign
    environment_variables = Column(JSON, nullable=True)
    
    # Phone numbers for calls
    call_numbers = Column(JSON, nullable=True)  # List of phone numbers
    
    # WhatsApp configuration
    whatsapp_numbers = Column(JSON, nullable=True)  # List of WhatsApp numbers
    whatsapp_webhook_url = Column(String(500), nullable=True)
    whatsapp_verify_token = Column(String(255), nullable=True)
    whatsapp_access_token = Column(String(500), nullable=True)
    
    # Campaign metrics
    total_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    total_whatsapp_messages = Column(Integer, default=0)
    total_conversations = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_call_duration = Column(Float, default=0.0)  # in seconds
    avg_response_time = Column(Float, default=0.0)  # in seconds
    total_cost = Column(Float, default=0.0)
    
    # Schedule
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    
    # Ownership
    owner_id = Column(Integer, ForeignKey("system_users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("SystemUser", back_populates="campaigns")
    agents = relationship("Agent", back_populates="campaign", cascade="all, delete-orphan")
    call_logs = relationship("CallLog", back_populates="campaign", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    def calculate_success_rate(self):
        """Calculate and update success rate"""
        if self.total_calls > 0:
            self.success_rate = (self.successful_calls / self.total_calls) * 100
        else:
            self.success_rate = 0.0
    
    def to_dict(self):
        """Convert campaign to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "slug": self.slug,
            "status": self.status,
            "is_active": self.is_active,
            "campaign_type": self.campaign_type,
            "target_audience": self.target_audience,
            "goals": self.goals,
            "environment_variables": self.environment_variables,
            "call_numbers": self.call_numbers,
            "whatsapp_numbers": self.whatsapp_numbers,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "total_whatsapp_messages": self.total_whatsapp_messages,
            "total_conversations": self.total_conversations,
            "success_rate": self.success_rate,
            "avg_call_duration": self.avg_call_duration,
            "avg_response_time": self.avg_response_time,
            "total_cost": self.total_cost,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }