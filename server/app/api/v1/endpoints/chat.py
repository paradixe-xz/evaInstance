"""
Chat API endpoints
"""

from typing import List
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....core.logging import get_logger
from ....core.exceptions import ChatHistoryError, ValidationError
from ....services.chat_service import ChatService
from ....repositories.user_repository import UserRepository
from ....repositories.chat_repository import ChatRepository, MessageRepository
from ....schemas.chat import (
    ChatHistoryRequest,
    ChatHistoryResponse,
    ActiveSessionsResponse,
    ChatStatsResponse,
    UserStatsRequest,
    UserStatsResponse,
    BulkMessageRequest,
    BulkMessageResponse,
    SendMessageRequest
)

logger = get_logger(__name__)
router = APIRouter()

# Initialize services
chat_service = ChatService()


@router.post("/message")
async def send_message(request: SendMessageRequest):
    """
    Send a message to a user
    """
    try:
        logger.info(f"Sending message to {request.phone_number}")
        
        result = chat_service.send_message(
            phone_number=request.phone_number,
            message=request.message
        )
        
        return result
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Send message error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")



@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    phone_number: str = Query(..., description="User phone number"),
    limit: int = Query(50, ge=1, le=100, description="Number of messages"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Get chat history for a specific user
    """
    try:
        logger.info(f"Getting chat history for {phone_number}")
        
        result = chat_service.get_chat_history(
            phone_number=phone_number,
            limit=limit,
            offset=offset
        )
        
        # DEBUG: Log media fields for first message
        if result.get("messages") and len(result["messages"]) > 0:
            first_msg = result["messages"][0]
            logger.info(f"🔍 DEBUG First message media fields: media_local_path={first_msg.get('media_local_path')}, media_filename={first_msg.get('media_filename')}, message_type={first_msg.get('message_type')}")
        
        return ChatHistoryResponse(**result)
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except ChatHistoryError as e:
        logger.error(f"Chat history error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")
        
    except Exception as e:
        logger.error(f"Get chat history error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/active-sessions", response_model=ActiveSessionsResponse)
async def get_active_sessions(
    limit: int = Query(20, ge=1, le=100, description="Number of sessions")
):
    """
    Get active chat sessions
    """
    try:
        logger.info("Getting active chat sessions")
        
        sessions = chat_service.get_active_sessions(limit=limit)
        
        return ActiveSessionsResponse(
            sessions=sessions,
            total=len(sessions)
        )
        
    except ChatHistoryError as e:
        logger.error(f"Chat history error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve active sessions")
        
    except Exception as e:
        logger.error(f"Get active sessions error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats", response_model=ChatStatsResponse)
async def get_chat_stats(db: Session = Depends(get_db)):
    """
    Get overall chat statistics
    """
    try:
        logger.info("Getting chat statistics")
        
        user_repo = UserRepository(db)
        chat_repo = ChatRepository(db)
        message_repo = MessageRepository(db)
        
        # Get statistics
        total_users = user_repo.count()
        active_users = user_repo.count_active_users()
        total_sessions = chat_repo.count_sessions()
        active_sessions = chat_repo.count_active_sessions()
        total_messages = message_repo.count()
        messages_today = message_repo.count_messages_today()
        
        # Calculate average response time (simplified)
        avg_response_time = message_repo.get_average_response_time()
        
        return ChatStatsResponse(
            total_users=total_users,
            active_users=active_users,
            total_sessions=total_sessions,
            active_sessions=active_sessions,
            total_messages=total_messages,
            messages_today=messages_today,
            avg_response_time=avg_response_time
        )
        
    except Exception as e:
        logger.error(f"Get chat stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user-stats", response_model=UserStatsResponse)
async def get_user_stats(
    phone_number: str = Query(..., description="User phone number"),
    db: Session = Depends(get_db)
):
    """
    Get statistics for a specific user
    """
    try:
        logger.info(f"Getting user statistics for {phone_number}")
        
        user_repo = UserRepository(db)
        chat_repo = ChatRepository(db)
        message_repo = MessageRepository(db)
        
        # Validate and get user
        from ....services.whatsapp_service import WhatsAppService
        whatsapp_service = WhatsAppService()
        formatted_phone = whatsapp_service.validate_phone_number(phone_number)
        
        user = user_repo.get_by_phone_number(formatted_phone)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user statistics
        user_stats = user_repo.get_user_stats(user.id)
        session_stats = chat_repo.get_user_session_stats(user.id)
        message_stats = message_repo.get_user_message_stats(user.id)
        
        return UserStatsResponse(
            user={
                "id": user.id,
                "phone_number": user.phone_number,
                "name": user.name,
                "is_active": user.is_active,
                "total_messages": user.total_messages,
                "last_activity": user.last_activity_date.isoformat() if user.last_activity_date else None
            },
            total_sessions=session_stats.get("total_sessions", 0),
            active_sessions=session_stats.get("active_sessions", 0),
            total_messages=message_stats.get("total_messages", 0),
            incoming_messages=message_stats.get("incoming_messages", 0),
            outgoing_messages=message_stats.get("outgoing_messages", 0),
            avg_session_duration=session_stats.get("avg_duration", None),
            last_session_at=session_stats.get("last_session_at", None)
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Get user stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/bulk-message", response_model=BulkMessageResponse)
async def send_bulk_message(request: BulkMessageRequest):
    """
    Send a message to multiple users
    """
    try:
        logger.info(f"Sending bulk message to {len(request.phone_numbers)} users")
        
        successful = []
        failed = []
        errors = []
        
        for phone_number in request.phone_numbers:
            try:
                result = chat_service.send_message(
                    phone_number=phone_number,
                    message=request.message
                )
                successful.append(phone_number)
                logger.info(f"Message sent successfully to {phone_number}")
                
            except Exception as e:
                error_msg = str(e)
                failed.append({
                    "phone_number": phone_number,
                    "error": error_msg
                })
                errors.append(f"{phone_number}: {error_msg}")
                logger.error(f"Failed to send message to {phone_number}: {error_msg}")
        
        return BulkMessageResponse(
            total_sent=len(successful),
            successful=successful,
            failed=failed,
            errors=errors
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Bulk message error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"Bulk message error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


from fastapi import UploadFile, File, Form
import csv
import io

@router.post("/bulk-template", response_model=BulkMessageResponse)
async def send_bulk_template(
    file: UploadFile = File(...),
    template_name: str = Form(...)
):
    """
    Send a template message to multiple users from CSV
    """
    try:
        logger.info(f"Processing bulk template '{template_name}' from CSV")
        
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        content = await file.read()
        try:
            decoded_content = content.decode('utf-8')
        except UnicodeDecodeError:
            decoded_content = content.decode('latin-1')
            
        csv_reader = csv.DictReader(io.StringIO(decoded_content))
        
        # Identify phone column
        headers = csv_reader.fieldnames
        if not headers:
            raise HTTPException(status_code=400, detail="CSV file is empty or invalid")
            
        phone_column = next(
            (h for h in headers if h.lower() in ['phone', 'phone_number', 'telefono', 'teléfono', 'celular', 'mobile', 'whatsapp']), 
            None
        )
        
        if not phone_column:
             raise HTTPException(status_code=400, detail=f"Could not find phone number column. Headers found: {headers}")
             
        successful = []
        failed = []
        errors = []
        
        for row in csv_reader:
            phone_number = row.get(phone_column)
            if not phone_number:
                continue
                
            try:
                # Clean phone number logic if needed, but service handles validation
                result = chat_service.send_template_message(
                    phone_number=phone_number,
                    template_name=template_name,
                    language_code="es" # Default to Spanish
                )
                successful.append(phone_number)
                logger.info(f"Template sent successfully to {phone_number}")
                
            except Exception as e:
                error_msg = str(e)
                failed.append({
                    "phone_number": phone_number,
                    "error": error_msg
                })
                errors.append(f"{phone_number}: {error_msg}")
                logger.error(f"Failed to send template to {phone_number}: {error_msg}")
        
        return BulkMessageResponse(
            total_sent=len(successful),
            successful=successful,
            failed=failed,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk template error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def end_chat_session(session_id: int, db: Session = Depends(get_db)):
    """
    End a chat session
    """
    try:
        logger.info(f"Ending chat session {session_id}")
        
        chat_repo = ChatRepository(db)
        
        session = chat_repo.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        chat_repo.end_session(session_id)
        
        return {"status": "success", "message": f"Session {session_id} ended"}
        
    except Exception as e:
        logger.error(f"End session error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users")
async def get_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Get list of users
    """
    try:
        logger.info("Getting users list")
        
        user_repo = UserRepository(db)
        
        if active_only:
            users = user_repo.get_active_users(limit=limit, offset=offset)
        else:
            users = user_repo.get_all(limit=limit, offset=offset)
        
        total = user_repo.count_active_users() if active_only else user_repo.count()
        
        return {
            "users": [
                {
                    "id": user.id,
                    "phone_number": user.phone_number,
                    "name": user.name,
                    "is_active": user.is_active,
                    "total_messages": user.total_messages,
                    "ai_paused": user.ai_paused,
                    "last_activity": user.last_activity_date.isoformat() if user.last_activity_date else None,
                    "created_at": user.created_at.isoformat()
                }
                for user in users
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/user/{user_id}/block")
async def block_user(user_id: int, db: Session = Depends(get_db)):
    """
    Block a user
    """
    try:
        logger.info(f"Blocking user {user_id}")
        
        user_repo = UserRepository(db)
        
        user = user_repo.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_repo.block_user(user_id)
        
        return {"status": "success", "message": f"User {user_id} blocked"}
        
    except Exception as e:
        logger.error(f"Block user error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/user/{user_id}/unblock")
async def unblock_user(user_id: int, db: Session = Depends(get_db)):
    """
    Unblock a user
    """
    try:
        logger.info(f"Unblocking user {user_id}")
        
        user_repo = UserRepository(db)
        
        user = user_repo.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_repo.unblock_user(user_id)
        
        return {"status": "success", "message": f"User {user_id} unblocked"}
        
    except Exception as e:
        logger.error(f"Unblock user error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


from pydantic import BaseModel

class AIStatusUpdate(BaseModel):
    ai_paused: bool

@router.patch("/user/{user_id}/ai-status")
async def update_ai_status(
    user_id: int, 
    status_update: AIStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update user's AI paused status
    """
    try:
        logger.info(f"Updating AI status for user {user_id} to {status_update.ai_paused}")
        
        user_repo = UserRepository(db)
        
        user = user_repo.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_repo.toggle_ai_status(user_id, status_update.ai_paused)
        
        return {"status": "success", "ai_paused": status_update.ai_paused}
        
    except Exception as e:
        logger.error(f"Update AI status error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")