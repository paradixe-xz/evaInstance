"""
Chat service for managing conversations and message processing
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.logging import get_logger
from ..core.exceptions import ChatHistoryError, ValidationError
from ..models.user import User
from ..models.chat import ChatSession, Message, MessageType, MessageDirection, ChatSessionStatus
from ..repositories.user_repository import UserRepository
from ..repositories.chat_repository import ChatRepository, MessageRepository
from .whatsapp_service import WhatsAppService
from .ollama_service import OllamaService

logger = get_logger(__name__)


class ChatService:
    """Service for managing chat conversations and message processing"""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
        self.ollama_service = OllamaService()
        
    def process_incoming_message(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming WhatsApp message
        
        Args:
            webhook_data: Raw webhook data from WhatsApp
            
        Returns:
            Processing result
        """
        try:
            # Parse webhook message
            parsed_message = self.whatsapp_service.parse_webhook_message(webhook_data)
            
            if not parsed_message or parsed_message.get("type") == "status":
                # Handle status updates
                if parsed_message and parsed_message.get("type") == "status":
                    self._handle_status_update(parsed_message)
                return {"status": "ignored", "reason": "Not a message or status update"}
            
            # Extract message details
            phone_number = parsed_message["from"]
            message_content = parsed_message.get("text", "")
            message_type = parsed_message.get("type", "text")
            whatsapp_message_id = parsed_message["message_id"]
            contact_name = parsed_message.get("contact", {}).get("name", "")
            
            logger.info(f"Processing message from {phone_number}: {message_content[:100]}")
            
            # Get database session
            db_generator = get_db()
            db = next(db_generator)
            try:
                user_repo = UserRepository(db)
                chat_repo = ChatRepository(db)
                message_repo = MessageRepository(db)
                
                # Get or create user
                user = user_repo.get_by_phone_number(phone_number)
                if not user:
                    # Use wa_id if available, otherwise use phone_number as whatsapp_id
                    whatsapp_id = parsed_message.get("contact", {}).get("wa_id") or phone_number
                    user = user_repo.create({
                        "phone_number": phone_number,
                        "whatsapp_id": whatsapp_id,
                        "name": contact_name or f"User {phone_number[-4:]}",
                        "is_active": True,
                        "language": "es"
                    })
                    logger.info(f"Created new user: {user.phone_number} with whatsapp_id: {whatsapp_id}")
                else:
                    # Update user activity
                    user_repo.update_last_activity(user.id)
                    if contact_name and not user.name:
                        user_repo.update(user.id, {"name": contact_name})
                
                # Get or create active chat session
                active_session = chat_repo.get_active_session_for_user(user.id)
                if not active_session:
                    # Generate unique session ID
                    session_id = f"session_{user.id}_{int(datetime.utcnow().timestamp())}"
                    active_session = chat_repo.create_session(
                        user_id=user.id,
                        session_id=session_id,
                        ai_personality="ana"
                    )
                    logger.info(f"Created new chat session: {active_session.id}")
                
                # Check if message already exists (prevent duplicates)
                existing_message = message_repo.get_by_whatsapp_id(whatsapp_message_id)
                if existing_message:
                    logger.info(f"📝 Message {whatsapp_message_id} already exists, skipping processing")
                    return {
                        "status": "duplicate",
                        "user_id": user.id,
                        "session_id": active_session.id,
                        "existing_message_id": existing_message.id,
                        "note": "Message already processed"
                    }
                
                # Save incoming message
                incoming_message = message_repo.create_message(
                    user_id=user.id,
                    chat_session_id=active_session.id,
                    content=message_content,
                    direction=MessageDirection.INCOMING,
                    message_type=message_type,
                    whatsapp_message_id=whatsapp_message_id,
                    raw_content=str(parsed_message)
                )
                
                # Mark WhatsApp message as read
                try:
                    self.whatsapp_service.mark_message_as_read(whatsapp_message_id)
                except Exception as e:
                    logger.warning(f"Failed to mark message as read: {str(e)}")
                
                # Generate AI response only for text messages
                if message_type == "text" and message_content.strip():
                    ai_response = self._generate_ai_response(
                        user, active_session, message_content, db
                    )
                    
                    if ai_response:
                        # Send AI response via WhatsApp
                        whatsapp_response = self.whatsapp_service.send_text_message(
                            phone_number, ai_response
                        )
                        
                        # Save outgoing message
                        outgoing_message = message_repo.create_message(
                            user_id=user.id,
                            chat_session_id=active_session.id,
                            content=ai_response,
                            direction=MessageDirection.OUTGOING,
                            message_type="text",
                            whatsapp_message_id=whatsapp_response.get("messages", [{}])[0].get("id"),
                            raw_content=str(whatsapp_response)
                        )
                        
                        # Update message processing info
                        processing_time = (datetime.utcnow() - incoming_message.timestamp).total_seconds()
                        message_repo.update_ai_processing(
                            incoming_message.id,
                            response_time=int(processing_time * 1000),  # Convert to milliseconds
                            confidence=95  # Default confidence
                        )
                        
                        logger.info(f"AI response sent to {phone_number}")
                        
                        return {
                            "status": "processed",
                            "user_id": user.id,
                            "session_id": active_session.id,
                            "incoming_message_id": incoming_message.id,
                            "outgoing_message_id": outgoing_message.id,
                            "ai_response": ai_response
                        }
                    else:
                        logger.warning(f"Failed to generate AI response for message from {phone_number}")
                        return {
                            "status": "processed",
                            "user_id": user.id,
                            "session_id": active_session.id,
                            "incoming_message_id": incoming_message.id,
                            "error": "Failed to generate AI response"
                        }
                else:
                    # Non-text message or empty content
                    logger.info(f"Received non-text message or empty content from {phone_number}")
                    return {
                        "status": "processed",
                        "user_id": user.id,
                        "session_id": active_session.id,
                        "incoming_message_id": incoming_message.id,
                        "note": "Non-text message received"
                    }
            finally:
                # Close database session
                try:
                    next(db_generator, None)  # Exhaust the generator to trigger cleanup
                except StopIteration:
                    pass
                    
        except Exception as e:
            error_msg = f"Error processing incoming message: {str(e)}"
            logger.error(error_msg)
            raise ChatHistoryError(error_msg, error_code="PROCESS_MESSAGE_FAILED")
    
    def _generate_ai_response(
        self,
        user: User,
        session: ChatSession,
        user_message: str,
        db: Session
    ) -> Optional[str]:
        """
        Generate AI response using Ollama
        
        Args:
            user: User object
            session: Chat session
            user_message: User's message
            db: Database session
            
        Returns:
            AI generated response or None if failed
        """
        try:
            message_repo = MessageRepository(db)
            
            # Get conversation context (last 10 messages)
            conversation_history = message_repo.get_conversation_context(
                session.id, max_messages=10
            )
            
            # Prepare user context
            user_context = {
                "name": user.name,
                "phone": user.phone_number,
                "language": user.language,
                "total_messages": user.total_messages,
                "session_started": session.started_at.isoformat() if session.started_at else None
            }
            
            # Generate AI response
            ai_response = self.ollama_service.generate_response(
                user_message=user_message,
                conversation_history=conversation_history,
                user_context=user_context
            )
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return None
    
    def _handle_status_update(self, status_data: Dict[str, Any]) -> None:
        """
        Handle WhatsApp message status updates
        
        Args:
            status_data: Status update data
        """
        try:
            message_id = status_data.get("message_id")
            status = status_data.get("status")
            
            if not message_id or not status:
                return
            
            with get_db() as db:
                message_repo = MessageRepository(db)
                
                if status == "delivered":
                    message_repo.mark_as_delivered(message_id)
                elif status == "read":
                    message_repo.mark_as_read(message_id)
                elif status == "failed":
                    message_repo.mark_as_failed(message_id)
                
                logger.info(f"Updated message {message_id} status to {status}")
                
        except Exception as e:
            logger.error(f"Error handling status update: {str(e)}")
    
    def send_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send a message to a user
        
        Args:
            phone_number: Recipient phone number
            message: Message content
            
        Returns:
            Send result
        """
        try:
            # Validate phone number
            formatted_phone = self.whatsapp_service.validate_phone_number(phone_number)
            
            # Send message via WhatsApp
            whatsapp_response = self.whatsapp_service.send_text_message(
                formatted_phone, message
            )
            
            with get_db() as db:
                user_repo = UserRepository(db)
                chat_repo = ChatRepository(db)
                message_repo = MessageRepository(db)
                
                # Get or create user
                user = user_repo.get_by_phone_number(formatted_phone)
                if not user:
                    user = user_repo.create({
                        "phone_number": formatted_phone,
                        "whatsapp_id": formatted_phone,
                        "name": f"User {formatted_phone[-4:]}",
                        "is_active": True,
                        "language": "es"
                    })
                
                # Get or create active session
                active_session = chat_repo.get_active_session(user.id)
                if not active_session:
                    active_session = chat_repo.create_session({
                        "user_id": user.id,
                        "status": ChatSessionStatus.ACTIVE,
                        "started_at": datetime.utcnow()
                    })
                
                # Save outgoing message
                outgoing_message = message_repo.create({
                    "session_id": active_session.id,
                    "whatsapp_message_id": whatsapp_response.get("messages", [{}])[0].get("id"),
                    "direction": MessageDirection.OUTGOING,
                    "message_type": MessageType.TEXT,
                    "content": message,
                    "metadata": {
                        "whatsapp_response": whatsapp_response,
                        "manual_send": True
                    },
                    "sent_at": datetime.utcnow()
                })
                
                return {
                    "status": "sent",
                    "user_id": user.id,
                    "session_id": active_session.id,
                    "message_id": outgoing_message.id,
                    "whatsapp_response": whatsapp_response
                }
                
        except Exception as e:
            error_msg = f"Error sending message to {phone_number}: {str(e)}"
            logger.error(error_msg)
            raise ChatHistoryError(error_msg, error_code="SEND_MESSAGE_FAILED")
    
    def get_chat_history(
        self,
        phone_number: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get chat history for a user
        
        Args:
            phone_number: User phone number
            limit: Number of messages to retrieve
            offset: Offset for pagination
            
        Returns:
            Chat history data
        """
        try:
            formatted_phone = self.whatsapp_service.validate_phone_number(phone_number)
            
            with get_db() as db:
                user_repo = UserRepository(db)
                message_repo = MessageRepository(db)
                
                user = user_repo.get_by_phone_number(formatted_phone)
                if not user:
                    return {
                        "user": None,
                        "messages": [],
                        "total": 0
                    }
                
                messages = message_repo.get_user_messages(
                    user.id, limit=limit, offset=offset
                )
                
                total_messages = message_repo.count_user_messages(user.id)
                
                return {
                    "user": {
                        "id": user.id,
                        "phone_number": user.phone_number,
                        "name": user.name,
                        "is_active": user.is_active,
                        "total_messages": user.total_messages,
                        "last_activity": user.last_activity.isoformat() if user.last_activity else None
                    },
                    "messages": [
                        {
                            "id": msg.id,
                            "direction": msg.direction.value,
                            "content": msg.content,
                            "message_type": msg.message_type.value,
                            "created_at": msg.created_at.isoformat(),
                            "sent_at": msg.sent_at.isoformat() if msg.sent_at else None,
                            "received_at": msg.received_at.isoformat() if msg.received_at else None,
                            "is_read": msg.is_read,
                            "is_delivered": msg.is_delivered
                        }
                        for msg in messages
                    ],
                    "total": total_messages,
                    "limit": limit,
                    "offset": offset
                }
                
        except Exception as e:
            error_msg = f"Error getting chat history for {phone_number}: {str(e)}"
            logger.error(error_msg)
            raise ChatHistoryError(error_msg, error_code="GET_HISTORY_FAILED")
    
    def get_active_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get active chat sessions
        
        Args:
            limit: Number of sessions to retrieve
            
        Returns:
            List of active sessions
        """
        try:
            with get_db() as db:
                chat_repo = ChatRepository(db)
                
                sessions = chat_repo.get_sessions_with_messages(
                    status=ChatSessionStatus.ACTIVE,
                    limit=limit
                )
                
                return [
                    {
                        "session_id": session.id,
                        "user": {
                            "id": session.user.id,
                            "phone_number": session.user.phone_number,
                            "name": session.user.name
                        },
                        "started_at": session.started_at.isoformat() if session.started_at else None,
                        "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
                        "message_count": session.message_count,
                        "status": session.status.value
                    }
                    for session in sessions
                ]
                
        except Exception as e:
            error_msg = f"Error getting active sessions: {str(e)}"
            logger.error(error_msg)
            raise ChatHistoryError(error_msg, error_code="GET_SESSIONS_FAILED")