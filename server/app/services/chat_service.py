"""
Chat service for managing conversations and message processing
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..core.database import get_db, get_db_context
from ..core.logging import get_logger
from ..core.exceptions import ChatHistoryError, ValidationError
from ..models.user import User
from ..models.chat import ChatSession, Message, MessageType, MessageDirection, ChatSessionStatus
from ..repositories.user_repository import UserRepository
from ..repositories.chat_repository import ChatRepository, MessageRepository
from ..repositories.agent_repository import AgentRepository
from .whatsapp_service import WhatsAppService
from .ollama_service import OllamaService
from .conversation_service import ConversationService

logger = get_logger(__name__)


class ChatService:
    """Service for managing chat conversations and message processing"""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
        self.ollama_service = OllamaService()
        self.conversation_service = ConversationService()
        
    def _get_or_create_chat_session(self, user_id: str):
        """
        Get an existing chat session or create a new one
        
        Args:
            user_id: User's WhatsApp ID
            
        Returns:
            ChatSession object
        """
        with get_db_context() as db:
            chat_repo = ChatRepository(db)
            user_repo = UserRepository(db)
            
            # Get or create user
            user = user_repo.get_by_whatsapp_id(user_id)
            if not user:
                user = user_repo.create({
                    "phone_number": user_id,
                    "whatsapp_id": user_id,
                    "name": f"User {user_id[-4:]}",
                    "is_active": True,
                    "language": "es"
                })
            
            # Get or create active session
            active_session = chat_repo.get_active_session_for_user(user.id)
            if not active_session:
                session_id = f"session_{user.id}_{int(datetime.utcnow().timestamp())}"
                active_session = chat_repo.create_session(
                    user_id=user.id,
                    session_id=session_id,
                    ai_personality="isa"
                )
            
            return active_session
    
    def _get_conversation_history(self, chat_session_id: int, limit: int = 10) -> List[Dict[str, str]]:
        """
        Get conversation history for a chat session
        
        Args:
            chat_session_id: ID of the chat session
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries with role and content
        """
        with get_db_context() as db:
            message_repo = MessageRepository(db)
            messages = message_repo.get_messages_by_session(
                chat_session_id=chat_session_id,
                limit=limit
            )
            
            return [
                {
                    "role": "user" if msg.direction == MessageDirection.INCOMING else "assistant",
                    "content": msg.content
                }
                for msg in messages
            ]
    
    def _save_message(
        self,
        chat_session_id: int,
        content: str,
        direction: str,
        message_type: str = "text",
        whatsapp_message_id: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> None:
        """
        Save a message to the database
        
        Args:
            chat_session_id: ID of the chat session
            content: Message content
            direction: Message direction (incoming/outgoing)
            message_type: Type of message (text, image, etc.)
            whatsapp_message_id: Optional WhatsApp message ID
            user_id: Optional user ID. If not provided, will try to get it from the chat session
        """
        try:
            with get_db_context() as db:
                message_repo = MessageRepository(db)
                chat_repo = ChatRepository(db)
                
                # If user_id is not provided, try to get it from the chat session
                if user_id is None:
                    chat_session = chat_repo.get(chat_session_id)
                    if chat_session:
                        user_id = chat_session.user_id
                
                if user_id is None:
                    raise ValueError("Could not determine user_id for message")
                
                message_repo.create_message(
                    user_id=user_id,
                    chat_session_id=chat_session_id,
                    content=content,
                    direction=direction,
                    message_type=message_type,
                    whatsapp_message_id=whatsapp_message_id
                )
                db.commit()
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            raise
    
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
                
            # Get user ID and message
            user_id = parsed_message.get("from")
            user_message = parsed_message.get("text", "").strip()
            
            if not user_id or not user_message:
                return {"status": "error", "reason": "Missing user ID or message"}
                
            # Determine next step based on user input
            next_step = self.conversation_service.get_next_step(user_id, user_message)
            
            # If we have a predefined message, send it and save it to database
            if next_step.get("message"):
                # Get or create chat session to save the message
                chat_session = self._get_or_create_chat_session(user_id)
                
                # Save the outgoing message to database
                self._save_message(
                    chat_session_id=chat_session.id,
                    content=next_step["message"],
                    direction=MessageDirection.OUTGOING,
                    message_type="text",
                    user_id=chat_session.user_id
                )
                
                # Send message via WhatsApp
                self.whatsapp_service.send_message(
                    to=user_id,
                    message=next_step["message"]
                )
                return {"status": "success", "next_step": next_step.get("next_step")}
                
            # Refresh conversation state after potential transitions
            conversation_state = self.conversation_service.get_conversation_state(user_id)
            logger.info(f"Conversation state for {user_id}: {conversation_state.get('current_step')}")
            
            # Check if AI is paused for this user
            with get_db_context() as db:
                user_repo = UserRepository(db)
                # user_id from webhook is the phone number/whatsapp_id
                user = user_repo.get_by_whatsapp_id(user_id)
                
                if user and user.ai_paused:
                    logger.info(f"AI is paused for user {user.phone_number}, skipping AI generation")
                    return {
                        "status": "ignored",
                        "user_id": user.id,
                        "reason": "AI paused for user"
                    }

            # If we're in AI conversation mode, generate a response using Ollama
            if conversation_state.get("current_step") == "ai_conversation":
                logger.info(f"Generating AI response for {user_id} with message: {user_message[:100]}")
                # Get conversation history from database
                chat_session = self._get_or_create_chat_session(user_id)
                history = self._get_conversation_history(chat_session.id)
                
                # Filter out any messages that mention seguros/insurance to avoid contamination
                # Also, if this is a new conversation (just started), don't use old history
                if history:
                    # Check if conversation just started (less than 2 messages in history)
                    if len(history) <= 2:
                        # For new conversations, start fresh - don't use old contaminated history
                        history = []
                        logger.info("New conversation detected, starting with clean history")
                    else:
                        # Filter out contaminated messages
                        history = [
                            msg for msg in history 
                            if not any(word in msg.get("content", "").lower() 
                                     for word in ["seguro", "insurance", "vive tranqui", "venzamos", "peludito", "seguros mundial"])
                        ]
                        logger.info(f"Filtered history, remaining messages: {len(history)}")
                
                # Save incoming message to database first
                self._save_message(
                    chat_session_id=chat_session.id,
                    content=user_message,
                    direction=MessageDirection.INCOMING,
                    message_type="text",
                    whatsapp_message_id=parsed_message.get("message_id"),
                    user_id=chat_session.user_id
                )
                
                # Generate AI response
                logger.info(f"Calling Ollama service with history length: {len(history) if history else 0}")
                response = self.ollama_service.generate_response(
                    user_message=user_message,
                    conversation_history=history,
                    user_context={
                        "phone": user_id,
                        "name": parsed_message.get("profile_name", "Usuario")
                    },
                    conversation_state=conversation_state
                )
                
                if not response:
                    logger.error(f"Empty response from Ollama for {user_id}")
                    response = "Lo siento, no pude generar una respuesta. ¿Podrías repetir tu mensaje?"
                
                logger.info(f"Generated response for {user_id}: {response[:100]}")
                
                # Save outgoing message to database
                self._save_message(
                    chat_session_id=chat_session.id,
                    content=response,
                    direction=MessageDirection.OUTGOING,
                    message_type="text",
                    user_id=chat_session.user_id
                )
                
                # Send response via WhatsApp
                self.whatsapp_service.send_message(
                    to=user_id,
                    message=response
                )
                
                logger.info(f"Response sent to {user_id} successfully")
                return {"status": "success", "response": response}
                
            return {"status": "success", "next_step": next_step.get("next_step")}
            
            # Extract message details
            phone_number = parsed_message["from"]
            message_content = parsed_message.get("text", "")
            message_type = parsed_message.get("type", "text")
            whatsapp_message_id = parsed_message["message_id"]
            contact_name = parsed_message.get("contact", {}).get("name", "")
            
            logger.info(f"Processing message from {phone_number}: {message_content[:100]}")
            
            # Get database session
            # Get database session
            with get_db_context() as db:
                user_repo = UserRepository(db)
                chat_repo = ChatRepository(db)
                message_repo = MessageRepository(db)
                agent_repo = AgentRepository(db)
                
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
                        ai_personality="isa"
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
                    # Get next message from conversation flow
                    flow_response = self.conversation_service.get_next_message(
                        user_id=str(user.id),
                        user_input=message_content
                    )
                    
                    # If flow has a message, use it; otherwise generate with AI
                    if flow_response.get("message"):
                        ai_response = flow_response["message"]
                    else:
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
        Generate AI response using Ollama with conversation flow context
        
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
            agent_repo = AgentRepository(db)
            
            # Get conversation context (last 10 messages)
            conversation_history = message_repo.get_conversation_context(
                session.id, max_messages=10
            )
            
            # Get current conversation state
            conversation_state = self.conversation_service.conversation_states.get(
                str(user.id), 
                {"current_step": "initial_greeting", "data": {}}
            )
            
            # Prepare user context with conversation state
            user_context = {
                "name": user.name,
                "phone": user.phone_number,
                "language": user.language,
                "total_messages": user.total_messages,
                "session_started": session.started_at.isoformat() if session.started_at else None,
                "conversation_state": conversation_state
            }
            
            # Attach meeting information if already scheduled
            if session.meeting_date or session.meeting_time or session.meeting_timezone:
                meeting_info = {}
                if session.meeting_date:
                    meeting_info["date"] = session.meeting_date.isoformat()
                if session.meeting_time:
                    meeting_info["time"] = session.meeting_time.strftime("%H:%M")
                if session.meeting_timezone:
                    meeting_info["timezone"] = session.meeting_timezone
                user_context["meeting"] = meeting_info
            
            # Attach agent workflow configuration if available
            agent = None
            try:
                agent = agent_repo.get_by_ollama_model_name(self.ollama_service.model)
            except Exception as e:
                logger.warning(f"Unable to fetch agent configuration for model {self.ollama_service.model}: {e}")
            
            if agent:
                user_context.setdefault("agent", {})
                user_context["agent"].update({
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "conversation_style": agent.conversation_style,
                    "workflow_steps": agent.workflow_steps,
                    "conversation_structure": agent.conversation_structure
                })
            
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
            
            with get_db_context() as db:
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
            
            with get_db_context() as db:
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
                    "chat_session_id": active_session.id,
                    "whatsapp_message_id": whatsapp_response.get("messages", [{}])[0].get("id"),
                    "direction": MessageDirection.OUTGOING,
                    "message_type": MessageType.TEXT,
                    "content": message,
                    "raw_content": str({
                        "whatsapp_response": whatsapp_response,
                        "manual_send": True
                    }),
                    "timestamp": datetime.utcnow(),
                    "user_id": user.id  # Required field
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
            
            with get_db_context() as db:
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
                
                # Reverse messages to return them in chronological order (oldest first)
                messages = messages[::-1]
                
                return {
                    "user": {
                        "id": user.id,
                        "phone_number": user.phone_number,
                        "name": user.name,
                        "is_active": user.is_active,
                        "total_messages": user.total_messages,
                        "last_activity": user.last_activity_date.isoformat() if user.last_activity_date else None
                    },
                    "messages": [
                        {
                            "id": msg.id,
                            "direction": msg.direction.value,
                            "content": msg.content,
                            "message_type": msg.message_type.value,
                            "created_at": msg.created_at.isoformat(),
                            "sent_at": msg.timestamp.isoformat() if msg.timestamp else None,
                            "received_at": msg.timestamp.isoformat() if msg.timestamp else None,
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
            with get_db_context() as db:
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