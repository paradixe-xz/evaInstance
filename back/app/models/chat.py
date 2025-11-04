"""
Chat models for conversation management
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from ..core.database import Base


class MessageType(str, Enum):
    """Message type enumeration"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    STICKER = "sticker"
    SYSTEM = "system"


class MessageDirection(str, Enum):
    """Message direction enumeration"""
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class ChatSessionStatus(str, Enum):
    """Chat session status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ChatSession(Base):
    """Chat session model for managing conversations"""
    
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Session metadata
    channel = Column(String(20), default="whatsapp")
    status = Column(SQLEnum(ChatSessionStatus), default=ChatSessionStatus.ACTIVE)
    title = Column(String(200), nullable=True)
    summary = Column(Text, nullable=True)
    
    # Session tracking
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    # Message counts
    total_messages = Column(Integer, default=0)
    user_messages = Column(Integer, default=0)
    ai_messages = Column(Integer, default=0)
    
    # AI context
    context_summary = Column(Text, nullable=True)
    ai_personality = Column(String(50), default="ana")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("Message", back_populates="chat_session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, session_id='{self.session_id}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert chat session to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "channel": self.channel,
            "status": self.status.value if self.status else None,
            "title": self.title,
            "summary": self.summary,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "total_messages": self.total_messages,
            "user_messages": self.user_messages,
            "ai_messages": self.ai_messages,
            "context_summary": self.context_summary,
            "ai_personality": self.ai_personality,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Message(Base):
    """Message model for individual messages"""
    
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chat_session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    
    # Message identification
    whatsapp_message_id = Column(String(100), unique=True, index=True, nullable=True)
    external_id = Column(String(150), unique=True, index=True, nullable=True)
    channel = Column(String(20), default="whatsapp")
    message_type = Column(SQLEnum(MessageType), default=MessageType.TEXT)
    direction = Column(SQLEnum(MessageDirection), nullable=False)
    
    # Message content
    content = Column(Text, nullable=False)
    subject = Column(String(255), nullable=True)
    raw_content = Column(Text, nullable=True)  # Original WhatsApp message data
    
    # Message metadata
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    is_delivered = Column(Boolean, default=False)
    is_failed = Column(Boolean, default=False)
    
    # AI processing
    ai_processed = Column(Boolean, default=False)
    ai_response_time = Column(Integer, nullable=True)  # Response time in milliseconds
    ai_confidence = Column(Integer, nullable=True)  # AI confidence score (0-100)
    
    # Media information (for non-text messages)
    media_url = Column(String(500), nullable=True)
    media_mime_type = Column(String(100), nullable=True)
    media_size = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="messages")
    chat_session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, type='{self.message_type}', direction='{self.direction}')>"
    
    def to_dict(self):
        """Convert message to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "chat_session_id": self.chat_session_id,
            "whatsapp_message_id": self.whatsapp_message_id,
            "external_id": self.external_id,
            "channel": self.channel,
            "message_type": self.message_type.value if self.message_type else None,
            "direction": self.direction.value if self.direction else None,
            "content": self.content,
            "subject": self.subject,
            "raw_content": self.raw_content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "is_read": self.is_read,
            "is_delivered": self.is_delivered,
            "is_failed": self.is_failed,
            "ai_processed": self.ai_processed,
            "ai_response_time": self.ai_response_time,
            "ai_confidence": self.ai_confidence,
            "media_url": self.media_url,
            "media_mime_type": self.media_mime_type,
            "media_size": self.media_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }