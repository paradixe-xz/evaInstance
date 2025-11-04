"""
API v1 package
"""

from fastapi import APIRouter
from .endpoints import whatsapp, chat, calls
from . import auth, campaigns, agents, knowledge

api_router = APIRouter()

# Include routers
api_router.include_router(whatsapp.router, prefix="/whatsapp", tags=["WhatsApp"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(calls.router, prefix="/calls", tags=["Calls"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["Campaigns"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge Base"])