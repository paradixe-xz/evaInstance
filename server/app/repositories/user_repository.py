"""
User repository for user-specific database operations
"""

from typing import Optional, List

from sqlalchemy.orm import Session
from datetime import datetime

from .base import BaseRepository
from ..models.user import User
from ..core.exceptions import DatabaseError


class UserRepository(BaseRepository[User]):
    """Repository for User model operations"""
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_phone_number(self, phone_number: str) -> Optional[User]:
        """Get user by phone number"""
        return self.get_by_field("phone_number", phone_number)
    
    def get_by_whatsapp_id(self, whatsapp_id: str) -> Optional[User]:
        """Get user by WhatsApp ID"""
        return self.get_by_field("whatsapp_id", whatsapp_id)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        return self.get_by_field("email", email)
    
    def create_user(
        self,
        phone_number: str,
        whatsapp_id: str,
        name: Optional[str] = None,
        profile_name: Optional[str] = None,
        language: str = "es",
        timezone: str = "America/Mexico_City"
    ) -> User:
        """Create a new user"""
        user_data = {
            "phone_number": phone_number,
            "whatsapp_id": whatsapp_id,
            "name": name,
            "profile_name": profile_name,
            "language": language,
            "timezone": timezone,
            "first_contact_date": datetime.utcnow(),
            "last_activity_date": datetime.utcnow()
        }
        return self.create(user_data)

    def create_whatsapp_user(
        self,
        phone_number: str,
        whatsapp_id: str,
        name: Optional[str] = None,
        profile_name: Optional[str] = None,
        language: str = "es",
        timezone: str = "America/Mexico_City"
    ) -> User:
        """Create a new WhatsApp user"""
        user_data = {
            "phone_number": phone_number,
            "whatsapp_id": whatsapp_id,
            "name": name,
            "profile_name": profile_name,
            "language": language,
            "timezone": timezone,
            "first_contact_date": datetime.utcnow(),
            "last_activity_date": datetime.utcnow(),
            "primary_channel": "whatsapp",
            "last_channel": "whatsapp"
        }
        return self.create(user_data)

    def create_email_user(
        self,
        email: str,
        name: Optional[str] = None,
        language: str = "es",
        timezone: str = "America/Mexico_City"
    ) -> User:
        """Create a new email user"""
        user_data = {
            "email": email,
            "name": name,
            "language": language,
            "timezone": timezone,
            "first_contact_date": datetime.utcnow(),
            "last_activity_date": datetime.utcnow(),
            "primary_channel": "email",
            "last_channel": "email"
        }
        return self.create(user_data)
    
    def update_last_activity(self, user_id: int) -> Optional[User]:
        """Update user's last activity date"""
        return self.update(user_id, {"last_activity_date": datetime.utcnow()})

    def update_last_channel(self, user_id: int, channel: str) -> Optional[User]:
        """Update user's last channel used"""
        return self.update(user_id, {"last_channel": channel, "last_activity_date": datetime.utcnow()})
    
    def increment_message_count(self, user_id: int) -> Optional[User]:
        """Increment user's total message count"""
        user = self.get(user_id)
        if user:
            new_count = (user.total_messages or 0) + 1
            return self.update(user_id, {
                "total_messages": new_count,
                "last_activity_date": datetime.utcnow()
            })
        return None
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users"""
        try:
            return self.db.query(User).filter(
                User.is_active == True,
                User.is_blocked == False
            ).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseError(f"Error getting active users: {str(e)}")
    
    def get_recent_users(self, days: int = 7, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users who were active in the last N days"""
        try:
            cutoff_date = datetime.utcnow() - datetime.timedelta(days=days)
            return self.db.query(User).filter(
                User.last_activity_date >= cutoff_date,
                User.is_active == True
            ).order_by(User.last_activity_date.desc()).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseError(f"Error getting recent users: {str(e)}")
    
    def block_user(self, user_id: int) -> Optional[User]:
        """Block a user"""
        return self.update(user_id, {"is_blocked": True})
    
    def unblock_user(self, user_id: int) -> Optional[User]:
        """Unblock a user"""
        return self.update(user_id, {"is_blocked": False})
    
    def deactivate_user(self, user_id: int) -> Optional[User]:
        """Deactivate a user"""
        return self.update(user_id, {"is_active": False})
    
    def search_users(self, query: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Search users by name or phone number"""
        try:
            search_pattern = f"%{query}%"
            return self.db.query(User).filter(
                (User.name.ilike(search_pattern)) |
                (User.profile_name.ilike(search_pattern)) |
                (User.phone_number.ilike(search_pattern))
            ).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseError(f"Error searching users: {str(e)}")
    
    def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics"""
        user = self.get(user_id)
        if not user:
            return {}
        
        try:
            # Get message count from related messages
            from ..models.chat import Message
            message_count = self.db.query(Message).filter(Message.user_id == user_id).count()
            
            # Get session count from related chat sessions
            from ..models.chat import ChatSession
            session_count = self.db.query(ChatSession).filter(ChatSession.user_id == user_id).count()
            
            return {
                "user_id": user_id,
                "total_messages": message_count,
                "total_sessions": session_count,
                "first_contact": user.first_contact_date.isoformat() if user.first_contact_date else None,
                "last_activity": user.last_activity_date.isoformat() if user.last_activity_date else None,
                "is_active": user.is_active,
                "is_blocked": user.is_blocked
            }
        except Exception as e:
            raise DatabaseError(f"Error getting user stats: {str(e)}")