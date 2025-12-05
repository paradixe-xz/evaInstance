"""
Webhooks management API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from datetime import datetime
import httpx

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.system_user import SystemUser
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# Pydantic models
class WebhookCreate(BaseModel):
    url: HttpUrl
    events: List[str]
    description: Optional[str] = None
    secret: Optional[str] = None
    active: bool = True


class WebhookUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    description: Optional[str] = None
    secret: Optional[str] = None
    active: Optional[bool] = None


class WebhookResponse(BaseModel):
    id: int
    url: str
    events: List[str]
    description: Optional[str]
    active: bool
    created_at: datetime
    last_triggered: Optional[datetime]
    
    class Config:
        from_attributes = True


# In-memory webhook storage (in production, use database)
webhooks_store: dict = {}
webhook_logs_store: list = []
webhook_id_counter = 1


@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks(
    active_only: bool = Query(False, description="Only show active webhooks"),
    current_user: SystemUser = Depends(get_current_user)
):
    """List all webhooks for the current user"""
    user_webhooks = [
        wh for wh in webhooks_store.values()
        if wh.get("user_id") == current_user.id
    ]
    
    if active_only:
        user_webhooks = [wh for wh in user_webhooks if wh.get("active", True)]
    
    return user_webhooks


@router.post("/", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook: WebhookCreate,
    current_user: SystemUser = Depends(get_current_user)
):
    """Create a new webhook"""
    global webhook_id_counter
    
    webhook_data = {
        "id": webhook_id_counter,
        "url": str(webhook.url),
        "events": webhook.events,
        "description": webhook.description,
        "secret": webhook.secret,
        "active": webhook.active,
        "user_id": current_user.id,
        "created_at": datetime.utcnow(),
        "last_triggered": None
    }
    
    webhooks_store[webhook_id_counter] = webhook_data
    webhook_id_counter += 1
    
    logger.info(f"Created webhook {webhook_data['id']} for user {current_user.id}")
    
    return webhook_data


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    current_user: SystemUser = Depends(get_current_user)
):
    """Get a specific webhook"""
    webhook = webhooks_store.get(webhook_id)
    
    if not webhook or webhook.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    return webhook


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    webhook_update: WebhookUpdate,
    current_user: SystemUser = Depends(get_current_user)
):
    """Update a webhook"""
    webhook = webhooks_store.get(webhook_id)
    
    if not webhook or webhook.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    # Update fields
    update_data = webhook_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "url":
            webhook[field] = str(value)
        else:
            webhook[field] = value
    
    logger.info(f"Updated webhook {webhook_id}")
    
    return webhook


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: int,
    current_user: SystemUser = Depends(get_current_user)
):
    """Delete a webhook"""
    webhook = webhooks_store.get(webhook_id)
    
    if not webhook or webhook.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    del webhooks_store[webhook_id]
    logger.info(f"Deleted webhook {webhook_id}")


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    background_tasks: BackgroundTasks,
    current_user: SystemUser = Depends(get_current_user)
):
    """Test a webhook by sending a test event"""
    webhook = webhooks_store.get(webhook_id)
    
    if not webhook or webhook.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    if not webhook.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook is not active"
        )
    
    # Send test event in background
    test_payload = {
        "event": "webhook.test",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "message": "This is a test webhook event"
        }
    }
    
    background_tasks.add_task(
        trigger_webhook,
        webhook_id=webhook_id,
        event="webhook.test",
        payload=test_payload
    )
    
    return {"message": "Test webhook triggered", "webhook_id": webhook_id}


@router.get("/{webhook_id}/logs")
async def get_webhook_logs(
    webhook_id: int,
    limit: int = Query(50, ge=1, le=100),
    current_user: SystemUser = Depends(get_current_user)
):
    """Get logs for a specific webhook"""
    webhook = webhooks_store.get(webhook_id)
    
    if not webhook or webhook.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    # Filter logs for this webhook
    webhook_logs = [
        log for log in webhook_logs_store
        if log.get("webhook_id") == webhook_id
    ]
    
    # Sort by timestamp descending and limit
    webhook_logs.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
    
    return {
        "webhook_id": webhook_id,
        "logs": webhook_logs[:limit],
        "total": len(webhook_logs)
    }


# Helper function to trigger webhooks
async def trigger_webhook(webhook_id: int, event: str, payload: dict, max_retries: int = 3):
    """
    Trigger a webhook with retry logic
    
    Args:
        webhook_id: Webhook ID
        event: Event name
        payload: Event payload
        max_retries: Maximum retry attempts
    """
    webhook = webhooks_store.get(webhook_id)
    
    if not webhook or not webhook.get("active", True):
        return
    
    # Check if webhook is subscribed to this event
    if event not in webhook.get("events", []) and "*" not in webhook.get("events", []):
        return
    
    url = webhook.get("url")
    secret = webhook.get("secret")
    
    headers = {"Content-Type": "application/json"}
    if secret:
        headers["X-Webhook-Secret"] = secret
    
    # Retry logic
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                # Log the attempt
                log_entry = {
                    "webhook_id": webhook_id,
                    "event": event,
                    "timestamp": datetime.utcnow(),
                    "attempt": attempt + 1,
                    "status_code": response.status_code,
                    "success": response.status_code < 400
                }
                webhook_logs_store.append(log_entry)
                
                if response.status_code < 400:
                    # Success
                    webhook["last_triggered"] = datetime.utcnow()
                    logger.info(f"Webhook {webhook_id} triggered successfully for event {event}")
                    return
                else:
                    logger.warning(f"Webhook {webhook_id} returned {response.status_code}, attempt {attempt + 1}")
        
        except Exception as e:
            logger.error(f"Webhook {webhook_id} failed: {e}, attempt {attempt + 1}")
            log_entry = {
                "webhook_id": webhook_id,
                "event": event,
                "timestamp": datetime.utcnow(),
                "attempt": attempt + 1,
                "error": str(e),
                "success": False
            }
            webhook_logs_store.append(log_entry)
    
    logger.error(f"Webhook {webhook_id} failed after {max_retries} attempts")


# Available events
AVAILABLE_EVENTS = [
    "agent.created",
    "agent.updated",
    "agent.deleted",
    "message.received",
    "message.sent",
    "call.started",
    "call.ended",
    "campaign.started",
    "campaign.completed",
    "document.uploaded",
    "document.processed",
    "*"  # All events
]


@router.get("/events/available")
async def get_available_events():
    """Get list of available webhook events"""
    return {
        "events": AVAILABLE_EVENTS,
        "description": {
            "agent.*": "Agent lifecycle events",
            "message.*": "Message events",
            "call.*": "Call events",
            "campaign.*": "Campaign events",
            "document.*": "Document events",
            "*": "Subscribe to all events"
        }
    }
