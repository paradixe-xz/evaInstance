"""
User model for WhatsApp users
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship

from ..core.database import Base


class User(Base):
    """User model for WhatsApp users"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    whatsapp_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    profile_name = Column(String(100), nullable=True)
    
    # User status and preferences
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    language = Column(String(10), default="es")
    timezone = Column(String(50), default="America/Mexico_City")
    
    # Metadata
    first_contact_date = Column(DateTime, default=datetime.utcnow)
    last_activity_date = Column(DateTime, default=datetime.utcnow)
    total_messages = Column(Integer, default=0)
    
    # Additional user information
    notes = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)  # JSON string for tags
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, phone_number='{self.phone_number}', name='{self.name}')>"
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            "id": self.id,
            "phone_number": self.phone_number,
            "whatsapp_id": self.whatsapp_id,
            "name": self.name,
            "profile_name": self.profile_name,
            "is_active": self.is_active,
            "is_blocked": self.is_blocked,
            "language": self.language,
            "timezone": self.timezone,
            "first_contact_date": self.first_contact_date.isoformat() if self.first_contact_date else None,
            "last_activity_date": self.last_activity_date.isoformat() if self.last_activity_date else None,
            "total_messages": self.total_messages,
            "notes": self.notes,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }