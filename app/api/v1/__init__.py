"""
API v1 package
"""

from fastapi import APIRouter
from .endpoints import whatsapp, chat, calls

# Create API v1 router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    whatsapp.router,
    prefix="/whatsapp",
    tags=["WhatsApp"]
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"]
)

api_router.include_router(
    calls.router,
    prefix="/calls",
    tags=["Calls"]
)