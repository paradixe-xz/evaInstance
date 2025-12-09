"""
Chat service for managing conversations and message processing
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os
import re
from pypdf import PdfReader
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
    
    def _extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """
        Extract text from PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text or None
        """
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return None

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
                
            # Get user ID and message details
            user_id = parsed_message.get("from")
            message_type = parsed_message.get("type", "text")
            user_message = parsed_message.get("text", "").strip()
            contact_name = parsed_message.get("contact", {}).get("name", "")
            whatsapp_message_id = parsed_message.get("message_id")
            
            if not user_id:
                return {"status": "error", "reason": "Missing user ID"}

            # --- Media Handling (Incoming) ---
            additional_context = ""
            media_metadata = None  # Initialize for all message types
            
            if message_type == "document":
                document = parsed_message.get("document", {})
                mime_type = document.get("mime_type", "")
                
                if "application/pdf" in mime_type:
                    media_id = document.get("id")
                    filename = document.get("filename", "document.pdf")
                    caption = document.get("caption", "")
                    
                    # Download and extract text
                    media_url = self.whatsapp_service.get_media_url(media_id)
                    if media_url:
                        temp_dir = "temp_media"
                        if not os.path.exists(temp_dir):
                            os.makedirs(temp_dir)
                            
                        file_path = f"{temp_dir}/{media_id}_{filename}"
                        if self.whatsapp_service.download_media(media_url, file_path):
                            # Store media metadata for database
                            media_metadata = {
                                "url": document.get("url", media_url),
                                "mime_type": mime_type,
                                "local_path": file_path,
                                "filename": filename
                            }
                            
                            extracted_text = self._extract_text_from_pdf(file_path)
                            if extracted_text:
                                # Truncate if too long (e.g., 2000 chars)
                                additional_context = f"\n[SYSTEM: The user sent a PDF document named '{filename}'. Extracted Content: {extracted_text[:2000]}...]"
                                logger.info(f"Extracted text from PDF {filename}")
                            
                            # Add download link to message content
                            media_link = f"📄 Descargar PDF: /api/v1/media/{media_id}_{filename}"
                            if caption:
                                user_message = f"{caption}\n{media_link}"
                            else:
                                user_message = f"[PDF: {filename}]\n{media_link}"
                        else:
                            if caption:
                                user_message = f"{caption} (PDF - download failed)"
                            else:
                                user_message = f"[PDF: {filename} - download failed]"
                    else:
                        if caption:
                            user_message = f"{caption} (PDF attached)"
                        else:
                            user_message = f"[PDF: {filename}]"
            
            elif message_type == "image":
                image = parsed_message.get("image", {})
                caption = image.get("caption", "")
                media_id = image.get("id")
                mime_type = image.get("mime_type", "image/jpeg")
                
                logger.info(f"Processing image message with ID: {media_id}")
                
                # Download image
                media_url = self.whatsapp_service.get_media_url(media_id)
                if media_url:
                    temp_dir = "temp_media"
                    if not os.path.exists(temp_dir):
                        os.makedirs(temp_dir)
                    
                    # Extension inference (simplified)
                    file_path = f"{temp_dir}/{media_id}.jpg"
                    if self.whatsapp_service.download_media(media_url, file_path):
                        # Store media metadata for database
                        media_metadata = {
                            "url": image.get("url", media_url),
                            "mime_type": mime_type,
                            "local_path": file_path,
                            "filename": f"{media_id}.jpg"
                        }
                        
                        logger.info(f"Image downloaded to {file_path}")
                        # In the future, pass file_path to Vision model
                        additional_context = "\n[SYSTEM: The user sent an image. Treat it as if you received a photo.]"
                        
                        # Add link to message content
                        media_link = f"📷 Ver imagen: /api/v1/media/{media_id}.jpg"
                        if caption:
                            user_message = f"{caption}\n{media_link}"
                        else:
                            user_message = f"[Imagen recibida]\n{media_link}"
                    else:
                        logger.warning(f"Failed to download image {media_id}")
                        additional_context = "\n[SYSTEM: The user sent an image, but download failed.]"
                        if caption:
                            user_message = f"{caption} (Image - download failed)"
                        else:
                            user_message = "[Image received - download failed]"
                else:
                    if caption:
                        user_message = f"{caption} (Image attached)"
                    else:
                        user_message = "[Image received]"
                
            logger.info(f"Message processed. Type: {message_type}, User: {user_id}, Content: {user_message[:50]}")
                
            # Determine next step based on user input (flow vs AI)
            # Only use flow logic for explicit text commands or if we are not in media mode
            # For now, let's assume media always goes to AI/Agent unless flow strictly intercepts
            
            # Combine message for AI
            full_user_message = user_message
            if additional_context:
                full_user_message += additional_context
            
            # Get database session
            with get_db_context() as db:
                user_repo = UserRepository(db)
                chat_repo = ChatRepository(db)
                message_repo = MessageRepository(db)
                
                # Get or create user
                user = user_repo.get_by_phone_number(user_id)
                if not user:
                    whatsapp_id = parsed_message.get("contact", {}).get("wa_id") or user_id
                    user = user_repo.create({
                        "phone_number": user_id,
                        "whatsapp_id": whatsapp_id,
                        "name": contact_name or f"User {user_id[-4:]}",
                        "is_active": True,
                        "language": "es"
                    })
                else:
                    user_repo.update_last_activity(user.id)
                    if contact_name and not user.name:
                        user_repo.update(user.id, {"name": contact_name})
                
                # Get or create active chat session
                active_session = chat_repo.get_active_session_for_user(user.id)
                if not active_session:
                    session_id = f"session_{user.id}_{int(datetime.utcnow().timestamp())}"
                    active_session = chat_repo.create_session(
                        user_id=user.id,
                        session_id=session_id,
                        ai_personality="isa"
                    )
                
                # Check duplication
                existing_message = message_repo.get_by_whatsapp_id(whatsapp_message_id)
                if existing_message:
                    return {"status": "duplicate", "note": "Message already processed"}
                
                # Save incoming message
                # Map incoming media type to MessageType enum if possible, or fallback to TEXT/IMAGE
                # Since we updated models, we trust simple strings or Enum
                db_message_type = message_type if message_type in ["text", "image", "document", "template"] else "text"
                
                # Prepare media fields if available
                media_fields = {}
                if media_metadata:
                    media_fields = {
                        "media_url": media_metadata.get("url"),
                        "media_mime_type": media_metadata.get("mime_type"),
                        "media_local_path": media_metadata.get("local_path"),
                        "media_filename": media_metadata.get("filename")
                    }
                
                incoming_message = message_repo.create_message(
                    user_id=user.id,
                    chat_session_id=active_session.id,
                    content=user_message, # Display friendly text
                    direction=MessageDirection.INCOMING,
                    message_type=db_message_type,
                    whatsapp_message_id=whatsapp_message_id,
                    raw_content=str(parsed_message),
                    **media_fields
                )
                
                # Mark as read
                try:
                    self.whatsapp_service.mark_message_as_read(whatsapp_message_id)
                except Exception:
                    pass
                
                # Check AI Paused
                if user.ai_paused:
                    return {"status": "ignored", "reason": "AI paused"}
                
                # Generate AI Response
                # We use full_user_message (with Context) for AI
                
                # Get conversation history
                history = self._get_conversation_history(active_session.id)
                # ... history filtering logic ...
                if history and len(history) <= 2:
                    history = []
                else:
                     history = [m for m in history if not any(w in m.get("content","").lower() for w in ["seguro", "insurance", "vive tranqui"])]
                
                # Call Ollama
                # Pass image path if available for vision models
                image_path_for_vision = None
                if media_metadata and media_metadata.get("local_path"):
                    image_path_for_vision = media_metadata.get("local_path")
                    logger.info(f"🖼️ Passing image to vision model: {image_path_for_vision}")
                
                response = self.ollama_service.generate_response(
                    user_message=full_user_message,
                    conversation_history=history,
                    user_context={
                        "phone": user_id,
                        "name": user.name
                    },
                    conversation_state={"current_step": "ai_conversation"},
                    image_path=image_path_for_vision
                )
                
                if not response:
                    return {"status": "error", "error": "Empty AI response"}
                
                # --- Media Handling (Outgoing / Hands) ---
                # Check for [SEND_DOC: url] or [SEND_IMG: url] commands
                # Regex patterns
                doc_pattern = r'\[SEND_DOC:\s*(.+?)\]'
                img_pattern = r'\[SEND_IMG:\s*(.+?)\]'
                
                media_sends = []
                
                # Find documents
                for match in re.finditer(doc_pattern, response):
                    url = match.group(1).strip()
                    media_sends.append({"type": "document", "url": url})
                
                # Find images
                for match in re.finditer(img_pattern, response):
                    url = match.group(1).strip()
                    media_sends.append({"type": "image", "url": url})
                
                # Remove tags from response text
                clean_response = re.sub(doc_pattern, '', response)
                clean_response = re.sub(img_pattern, '', clean_response).strip()
                
                # Send Text Response (if any remains)
                if clean_response:
                    self.whatsapp_service.send_text_message(user_id, clean_response)
                    
                    # Save text message
                    self._save_message(
                        chat_session_id=active_session.id,
                        content=clean_response,
                        direction=MessageDirection.OUTGOING,
                        message_type="text",
                        user_id=user.id
                    )
                
                # Send Media Files
                for media in media_sends:
                    if media["type"] == "document":
                        # Attempt to derive filename from url or default
                        filename = media["url"].split("/")[-1] or "document.pdf"
                        self.whatsapp_service.send_document_message(user_id, media["url"], filename=filename)
                        
                        self._save_message(
                            chat_session_id=active_session.id,
                            content=f"[Sent Document: {filename}]",
                            direction=MessageDirection.OUTGOING,
                            message_type="document",
                            user_id=user.id
                        )
                        
                    elif media["type"] == "image":
                        self.whatsapp_service.send_image_message(user_id, media["url"])
                        
                        self._save_message(
                            chat_session_id=active_session.id,
                            content=f"[Sent Image]",
                            direction=MessageDirection.OUTGOING,
                            message_type="image",
                            user_id=user.id
                        )
                
                return {"status": "success", "response": clean_response}

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
                
                db.commit()
                
                return {
                    "status": "success", 
                    "message_id": outgoing_message.id,
                    "whatsapp_id": outgoing_message.whatsapp_message_id
                }
        except Exception as e:
            logger.error(f"Send message error: {str(e)}")
            raise

    def send_template_message(
        self, 
        phone_number: str, 
        template_name: str, 
        language_code: str = "es",
        parameters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send a template message to a user
        
        Args:
            phone_number: Recipient phone number
            template_name: Template name
            language_code: Language code (default: es)
            parameters: Template parameters
            
        Returns:
            Send result
        """
        try:
            # Validate phone number
            formatted_phone = self.whatsapp_service.validate_phone_number(phone_number)
            
            # Send template via WhatsApp
            whatsapp_response = self.whatsapp_service.send_template_message(
                to=formatted_phone,
                template_name=template_name,
                language_code=language_code,
                parameters=parameters
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
                        "language": language_code
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
                content = f"[Template: {template_name}]"
                if parameters:
                    content += f" Params: {', '.join(parameters)}"

                outgoing_message = message_repo.create({
                    "chat_session_id": active_session.id,
                    "whatsapp_message_id": whatsapp_response.get("messages", [{}])[0].get("id"),
                    "direction": MessageDirection.OUTGOING,
                    "message_type": MessageType.TEMPLATE,
                    "content": content,
                    "raw_content": str({
                        "whatsapp_response": whatsapp_response,
                        "template_name": template_name,
                        "parameters": parameters,
                        "bulk_send": True
                    }),
                    "timestamp": datetime.utcnow(),
                    "user_id": user.id
                })
                
                db.commit()
                
                return {
                    "status": "success", 
                    "message_id": outgoing_message.id,
                    "whatsapp_id": outgoing_message.whatsapp_message_id
                }
        except Exception as e:
            logger.error(f"Send template message error: {str(e)}")
            raise
    
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