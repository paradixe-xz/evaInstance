"""
API v1 package
"""

from fastapi import APIRouter

api_router = APIRouter()

def init_routers():
    """Initialize all API routers to avoid circular imports"""
    from .endpoints import whatsapp, chat, calls, sip, email, media
    from .endpoints.conversation_flows import router as conversation_flows_router
    from . import auth, campaigns, agents, knowledge, analytics, health, webhooks
    
    # Include routers
    api_router.include_router(whatsapp.router, prefix="/whatsapp", tags=["WhatsApp"])
    api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
    api_router.include_router(media.router, prefix="/media", tags=["Media"])
    api_router.include_router(calls.router, prefix="/calls", tags=["Calls"])
    api_router.include_router(sip.router, prefix="/sip", tags=["SIP Trunks"])
    api_router.include_router(email.router, prefix="/email", tags=["Email"])
    api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    api_router.include_router(campaigns.router, prefix="/campaigns", tags=["Campaigns"])
    api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
    api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge Base"])
    api_router.include_router(conversation_flows_router, prefix="/conversation-flows", tags=["Conversation Flows"])
    api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
    api_router.include_router(health.router, prefix="/health", tags=["Health"])
    api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])

# Initialize the routers
init_routers()