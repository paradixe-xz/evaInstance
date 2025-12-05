"""
Call Log model for tracking agent calls
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship

from ..core.database import Base


class CallLog(Base):
    """Call Log model for tracking agent calls"""
    
    __tablename__ = "call_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Call identification
    call_id = Column(String(100), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), nullable=False)
    
    # Call status and outcome
    status = Column(String(20), nullable=False)  # initiated, ringing, answered, completed, failed, busy, no_answer
    outcome = Column(String(50), nullable=True)  # successful, unsuccessful, callback_requested, not_interested
    
    # Call timing
    initiated_at = Column(DateTime, default=datetime.utcnow)
    answered_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration = Column(Float, default=0.0)  # in seconds
    
    # Call content and analysis
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    sentiment_score = Column(Float, nullable=True)  # -1 to 1
    keywords = Column(JSON, nullable=True)  # List of extracted keywords
    
    # Agent performance
    agent_response_time = Column(Float, nullable=True)  # average response time in seconds
    conversation_quality_score = Column(Float, nullable=True)  # 0 to 10
    customer_satisfaction = Column(Integer, nullable=True)  # 1 to 5 stars
    
    # Cost tracking
    cost = Column(Float, default=0.0)
    llm_tokens_used = Column(Integer, default=0)
    llm_cost = Column(Float, default=0.0)
    voice_cost = Column(Float, default=0.0)
    
    # Follow-up and notes
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # List of tags
    
    # Relationships
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agent = relationship("Agent", back_populates="call_logs")
    campaign = relationship("Campaign", back_populates="call_logs")
    
    def __repr__(self):
        return f"<CallLog(id={self.id}, call_id='{self.call_id}', status='{self.status}')>"
    
    def calculate_duration(self):
        """Calculate call duration if not set"""
        if self.answered_at and self.ended_at:
            self.duration = (self.ended_at - self.answered_at).total_seconds()
    
    def is_successful(self) -> bool:
        """Check if call was successful"""
        return self.outcome in ["successful", "callback_requested"]
    
    def to_dict(self):
        """Convert call log to dictionary"""
        return {
            "id": self.id,
            "call_id": self.call_id,
            "phone_number": self.phone_number,
            "status": self.status,
            "outcome": self.outcome,
            "initiated_at": self.initiated_at.isoformat(),
            "answered_at": self.answered_at.isoformat() if self.answered_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration": self.duration,
            "transcript": self.transcript,
            "summary": self.summary,
            "sentiment_score": self.sentiment_score,
            "keywords": self.keywords,
            "agent_response_time": self.agent_response_time,
            "conversation_quality_score": self.conversation_quality_score,
            "customer_satisfaction": self.customer_satisfaction,
            "cost": self.cost,
            "llm_tokens_used": self.llm_tokens_used,
            "llm_cost": self.llm_cost,
            "voice_cost": self.voice_cost,
            "follow_up_required": self.follow_up_required,
            "follow_up_date": self.follow_up_date.isoformat() if self.follow_up_date else None,
            "notes": self.notes,
            "tags": self.tags,
            "agent_id": self.agent_id,
            "campaign_id": self.campaign_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }