"""
WhatsApp API endpoints
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request, Query, Depends, BackgroundTasks
from fastapi.responses import PlainTextResponse

from ....core.logging import get_logger
from ....core.exceptions import WhatsAppAPIError, ValidationError, ServiceUnavailableError
from ....services.chat_service import ChatService
from ....services.whatsapp_service import WhatsAppService
from ....schemas.whatsapp import (
    SendMessageRequest,
    SendMessageResponse,
    MessageProcessingResponse,
    TemplateMessageRequest,
    WebhookMessage
)

logger = get_logger(__name__)
router = APIRouter()

# Initialize services
chat_service = ChatService()
whatsapp_service = WhatsAppService()


@router.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(
    request: Request,
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """
    Verify WhatsApp webhook subscription
    """
    try:
        logger.info(f"Webhook verification request: mode={hub_mode}, token={hub_verify_token}")
        
        if not all([hub_mode, hub_verify_token, hub_challenge]):
            logger.warning("Missing webhook verification parameters")
            raise HTTPException(status_code=400, detail="Missing verification parameters")
        
        challenge = whatsapp_service.verify_webhook(hub_mode, hub_verify_token, hub_challenge)
        
        if challenge:
            logger.info("Webhook verification successful")
            return challenge
        else:
            logger.warning("Webhook verification failed")
            raise HTTPException(status_code=403, detail="Verification failed")
            
    except Exception as e:
        logger.error(f"Webhook verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/webhook", response_model=MessageProcessingResponse)
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Receive and process WhatsApp webhook messages
    Supports both WhatsApp Business API format and Meta test format (Facebook Messenger)
    """
    try:
        # Get raw JSON data
        webhook_data = await request.json()
        
        # LOGS DETALLADOS PARA DEBUG
        logger.info("🔥🔥🔥 WEBHOOK RECIBIDO 🔥🔥🔥")
        logger.info(f"📩 Raw webhook data: {webhook_data}")
        logger.info(f"📋 Headers: {dict(request.headers)}")
        logger.info(f"🌐 Client IP: {request.client.host}")
        logger.info(f"🔍 Object field: {webhook_data.get('object')}")
        logger.info(f"🔍 Field field: {webhook_data.get('field')}")
        
        # Check if it's a WhatsApp Business API message format
        if webhook_data.get("object"):
            entry = webhook_data.get("entry", [])
            if entry:
                changes = entry[0].get("changes", [])
                if changes:
                    value = changes[0].get("value", {})
                    messages = value.get("messages", [])
                    
                    if messages:
                        message = messages[0]
                        if message.get("type") == "text":
                            from_number = message.get("from")
                            text_body = message.get("text", {}).get("body", "")
                            
                            # Process message in background
                            background_tasks.add_task(_process_webhook_message, webhook_data)
                            
                            return MessageProcessingResponse(
                                status="received",
                                note="Message queued for processing"
                            )
        
        # Check if it's a Meta test format (Facebook Messenger style)
        elif webhook_data.get("field") == "messages":
            value = webhook_data.get("value", {})
            message_data = value.get("message", {})
            sender = value.get("sender", {})
            
            if message_data and sender:
                from_id = sender.get("id")
                text_body = message_data.get("text", "")
                message_id = message_data.get("mid", "")
                

                
                # Convert Meta test format to WhatsApp Business API format for processing
                converted_data = {
                    "object": "whatsapp_business_account",
                    "entry": [{
                        "id": "test_entry",
                        "changes": [{
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "test",
                                    "phone_number_id": "751069368080044"
                                },
                                "contacts": [{
                                    "profile": {
                                        "name": f"Meta Test User {from_id[-4:]}"
                                    },
                                    "wa_id": from_id
                                }],
                                "messages": [{
                                    "from": from_id,
                                    "id": message_id,
                                    "timestamp": value.get("timestamp", ""),
                                    "text": {"body": text_body},
                                    "type": "text"
                                }]
                            }
                        }]
                    }]
                }
                
                # Process converted message in background
                background_tasks.add_task(_process_webhook_message, converted_data)
                
                return MessageProcessingResponse(
                    status="received",
                    note="Meta test message queued for processing"
                )
        
        # Check for message_deliveries format
        elif webhook_data.get("field") == "message_deliveries":
            return MessageProcessingResponse(
                status="received",
                note="Message delivery notification processed"
            )
        
        # Check for message_reads format
        elif webhook_data.get("field") == "message_reads":
            return MessageProcessingResponse(
                status="received",
                note="Message read notification processed"
            )
        return MessageProcessingResponse(
            status="received",
            note="Webhook received - no messages to process"
        )
        
    except Exception as e:
        logger.error(f"❌ Error in webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def _process_webhook_message(webhook_data: Dict[str, Any]):
    """
    Background task to process webhook message
    """
    try:
        result = chat_service.process_incoming_message(webhook_data)
    except Exception as e:
        logger.error(f"Background message processing error: {str(e)}")


@router.post("/send-message", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest):
    """
    Send a text message to a WhatsApp user
    """
    try:
        logger.info(f"Sending message to {request.phone_number}")
        
        result = chat_service.send_message(
            phone_number=request.phone_number,
            message=request.message
        )
        
        return SendMessageResponse(**result)
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except WhatsAppAPIError as e:
        logger.error(f"WhatsApp API error: {str(e)}")
        raise HTTPException(status_code=502, detail="WhatsApp API error")
        
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable: {str(e)}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
        
    except Exception as e:
        logger.error(f"Send message error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/send-template", response_model=SendMessageResponse)
async def send_template_message(request: TemplateMessageRequest):
    """
    Send a template message to a WhatsApp user
    """
    try:
        logger.info(f"Sending template '{request.template_name}' to {request.phone_number}")
        
        # Format phone number
        formatted_phone = whatsapp_service.validate_phone_number(request.phone_number)
        
        # Send template message
        whatsapp_response = whatsapp_service.send_template_message(
            to=formatted_phone,
            template_name=request.template_name,
            language_code=request.language_code,
            parameters=request.parameters
        )
        
        # For template messages, we don't save to database automatically
        # as they are usually marketing/notification messages
        
        return SendMessageResponse(
            status="sent",
            user_id=0,  # Template messages don't require user context
            session_id=0,
            message_id=0,
            whatsapp_response=whatsapp_response
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except WhatsAppAPIError as e:
        logger.error(f"WhatsApp API error: {str(e)}")
        raise HTTPException(status_code=502, detail="WhatsApp API error")
        
    except Exception as e:
        logger.error(f"Send template error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/mark-read/{message_id}")
async def mark_message_read(message_id: str):
    """
    Mark a WhatsApp message as read
    """
    try:
        logger.info(f"Marking message {message_id} as read")
        
        result = whatsapp_service.mark_message_as_read(message_id)
        
        return {"status": "success", "result": result}
        
    except WhatsAppAPIError as e:
        logger.error(f"WhatsApp API error: {str(e)}")
        raise HTTPException(status_code=502, detail="WhatsApp API error")
        
    except Exception as e:
        logger.error(f"Mark read error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for WhatsApp service
    """
    try:
        # Check if we can make a basic request to WhatsApp API
        # This is a simple health check - in production you might want more comprehensive checks
        
        return {
            "status": "healthy",
            "service": "whatsapp",
            "timestamp": "2024-01-01T00:00:00Z"  # You can use datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.get("/media/{media_id}")
async def get_media_url(media_id: str):
    """
    Get media URL from WhatsApp media ID
    """
    try:
        logger.info(f"Getting media URL for {media_id}")
        
        media_url = whatsapp_service.get_media_url(media_id)
        
        if media_url:
            return {"media_id": media_id, "url": media_url}
        else:
            raise HTTPException(status_code=404, detail="Media not found")
            
    except WhatsAppAPIError as e:
        logger.error(f"WhatsApp API error: {str(e)}")
        raise HTTPException(status_code=502, detail="WhatsApp API error")
        
    except Exception as e:
        logger.error(f"Get media error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")