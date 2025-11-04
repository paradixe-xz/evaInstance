"""
Chat repository for chat and message-specific database operations
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_, func
from datetime import datetime, timedelta

from .base import BaseRepository
from ..models.chat import ChatSession, Message, MessageDirection, ChatSessionStatus
from ..models.user import User
from ..core.exceptions import DatabaseError


class ChatRepository(BaseRepository[ChatSession]):
    """Repository for ChatSession model operations"""
    
    def __init__(self, db: Session):
        super().__init__(ChatSession, db)
    
    def create_session(
        self,
        user_id: int,
        session_id: str,
        ai_personality: str = "ema",
        channel: str = "whatsapp"
    ) -> ChatSession:
        """Create a new chat session"""
        session_data = {
            "user_id": user_id,
            "session_id": session_id,
            "channel": channel,
            "ai_personality": ai_personality,
            "started_at": datetime.utcnow(),
            "last_activity_at": datetime.utcnow()
        }
        return self.create(session_data)
    
    def get_by_session_id(self, session_id: str) -> Optional[ChatSession]:
        """Get chat session by session ID"""
        return self.get_by_field("session_id", session_id)
    
    def get_active_session_for_user(
        self,
        user_id: int,
        channel: Optional[str] = None
    ) -> Optional[ChatSession]:
        """Get active chat session for a user"""
        try:
            query = self.db.query(ChatSession).filter(
                and_(
                    ChatSession.user_id == user_id,
                    ChatSession.status == ChatSessionStatus.ACTIVE
                )
            )

            if channel:
                query = query.filter(ChatSession.channel == channel)

            return query.order_by(desc(ChatSession.last_activity_at)).first()
        except Exception as e:
            raise DatabaseError(f"Error getting active session for user {user_id}: {str(e)}")
    
    def get_user_sessions(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChatSession]:
        """Get all sessions for a user"""
        try:
            return self.db.query(ChatSession).filter(
                ChatSession.user_id == user_id
            ).order_by(desc(ChatSession.last_activity_at)).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseError(f"Error getting sessions for user {user_id}: {str(e)}")
    
    def update_session_activity(self, session_id: str) -> Optional[ChatSession]:
        """Update session's last activity time"""
        session = self.get_by_session_id(session_id)
        if session:
            return self.update(session.id, {"last_activity_at": datetime.utcnow()})
        return None
    
    def end_session(self, session_id: str, summary: Optional[str] = None) -> Optional[ChatSession]:
        """End a chat session"""
        session = self.get_by_session_id(session_id)
        if session:
            update_data = {
                "status": ChatSessionStatus.COMPLETED,
                "ended_at": datetime.utcnow()
            }
            if summary:
                update_data["summary"] = summary
            return self.update(session.id, update_data)
        return None
    
    def get_session_with_messages(self, session_id: str) -> Optional[ChatSession]:
        """Get session with all its messages"""
        try:
            return self.db.query(ChatSession).options(
                joinedload(ChatSession.messages)
            ).filter(ChatSession.session_id == session_id).first()
        except Exception as e:
            raise DatabaseError(f"Error getting session with messages: {str(e)}")


class MessageRepository(BaseRepository[Message]):
    """Repository for Message model operations"""
    
    def __init__(self, db: Session):
        super().__init__(Message, db)
    
    def create_message(
        self,
        user_id: int,
        chat_session_id: int,
        content: str,
        direction: MessageDirection,
        message_type: str = "text",
        whatsapp_message_id: Optional[str] = None,
        raw_content: Optional[str] = None,
        channel: str = "whatsapp",
        external_id: Optional[str] = None,
        subject: Optional[str] = None
    ) -> Message:
        """Create a new message"""
        message_data = {
            "user_id": user_id,
            "chat_session_id": chat_session_id,
            "content": content,
            "direction": direction,
            "message_type": message_type,
            "whatsapp_message_id": whatsapp_message_id,
            "raw_content": raw_content,
            "timestamp": datetime.utcnow(),
            "channel": channel,
            "external_id": external_id,
            "subject": subject
        }
        return self.create(message_data)
    
    def get_by_whatsapp_id(self, whatsapp_message_id: str) -> Optional[Message]:
        """Get message by WhatsApp message ID"""
        return self.get_by_field("whatsapp_message_id", whatsapp_message_id)
    
    def get_by_external_id(self, external_id: str) -> Optional[Message]:
        """Get message by external provider ID (email, etc.)"""
        return self.get_by_field("external_id", external_id)
    
    def get_session_messages(
        self,
        session_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """Get messages for a chat session"""
        try:
            return self.db.query(Message).filter(
                Message.chat_session_id == session_id
            ).order_by(Message.timestamp).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseError(f"Error getting messages for session {session_id}: {str(e)}")
    
    def get_recent_messages(
        self,
        session_id: int,
        limit: int = 10
    ) -> List[Message]:
        """Get recent messages for context"""
        try:
            return self.db.query(Message).filter(
                Message.chat_session_id == session_id
            ).order_by(desc(Message.timestamp)).limit(limit).all()
        except Exception as e:
            raise DatabaseError(f"Error getting recent messages: {str(e)}")
    
    def get_user_messages(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """Get all messages for a user"""
        try:
            return self.db.query(Message).filter(
                Message.user_id == user_id
            ).order_by(desc(Message.timestamp)).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseError(f"Error getting messages for user {user_id}: {str(e)}")
    
    def mark_as_read(self, message_id: int) -> Optional[Message]:
        """Mark message as read"""
        return self.update(message_id, {"is_read": True})
    
    def mark_as_delivered(self, message_id: int) -> Optional[Message]:
        """Mark message as delivered"""
        return self.update(message_id, {"is_delivered": True})
    
    def mark_as_failed(self, message_id: int) -> Optional[Message]:
        """Mark message as failed"""
        return self.update(message_id, {"is_failed": True})
    
    def update_ai_processing(
        self,
        message_id: int,
        response_time: Optional[int] = None,
        confidence: Optional[int] = None
    ) -> Optional[Message]:
        """Update AI processing information"""
        update_data = {"ai_processed": True}
        if response_time is not None:
            update_data["ai_response_time"] = response_time
        if confidence is not None:
            update_data["ai_confidence"] = confidence
        return self.update(message_id, update_data)
    
    def get_conversation_context(
        self,
        session_id: int,
        max_messages: int = 20
    ) -> List[Dict[str, Any]]:
        """Get conversation context for AI processing"""
        try:
            messages = self.db.query(Message).filter(
                Message.chat_session_id == session_id
            ).order_by(desc(Message.timestamp)).limit(max_messages).all()
            
            # Reverse to get chronological order
            messages.reverse()
            
            context = []
            for msg in messages:
                context.append({
                    "role": "user" if msg.direction == MessageDirection.INCOMING else "assistant",
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                })
            
            return context
        except Exception as e:
            raise DatabaseError(f"Error getting conversation context: {str(e)}")
    
    def get_message_stats(self, session_id: int) -> Dict[str, Any]:
        """Get message statistics for a session"""
        try:
            total_messages = self.db.query(Message).filter(
                Message.chat_session_id == session_id
            ).count()
            
            user_messages = self.db.query(Message).filter(
                and_(
                    Message.chat_session_id == session_id,
                    Message.direction == MessageDirection.INCOMING
                )
            ).count()
            
            ai_messages = self.db.query(Message).filter(
                and_(
                    Message.chat_session_id == session_id,
                    Message.direction == MessageDirection.OUTGOING
                )
            ).count()
            
            avg_response_time = self.db.query(func.avg(Message.ai_response_time)).filter(
                and_(
                    Message.chat_session_id == session_id,
                    Message.ai_response_time.isnot(None)
                )
            ).scalar()
            
            return {
                "total_messages": total_messages,
                "user_messages": user_messages,
                "ai_messages": ai_messages,
                "avg_response_time": float(avg_response_time) if avg_response_time else None
            }
        except Exception as e:
            raise DatabaseError(f"Error getting message stats: {str(e)}")