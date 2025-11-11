"""
API v1 package
"""

from fastapi import APIRouter

api_router = APIRouter()

def init_routers():
    """Initialize all API routers to avoid circular imports"""
    from .endpoints import whatsapp, chat, calls
    from .endpoints.conversation_flows import router as conversation_flows_router
    from . import auth, campaigns, agents, knowledge
    
    # Include routers
    api_router.include_router(whatsapp.router, prefix="/whatsapp", tags=["WhatsApp"])
    api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
    api_router.include_router(calls.router, prefix="/calls", tags=["Calls"])
    api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    api_router.include_router(campaigns.router, prefix="/campaigns", tags=["Campaigns"])
    api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
    api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge Base"])
    api_router.include_router(conversation_flows_router, prefix="/conversation-flows", tags=["Conversation Flows"])

# Initialize the routers
init_routers()