"""
Main FastAPI application
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time
import uuid
import os

from .core.config import get_settings
from .core.logging import get_logger, setup_logging
from .core.database import init_db, close_db
from .core.exceptions import (
    WhatsAppAIException,
    WhatsAppAPIError,
    OllamaError,
    ChatHistoryError,
    ValidationError,
    ServiceUnavailableError
)
from .middleware import LoggingMiddleware
from .api.v1 import api_router

# Setup logging with console output enabled for debugging
setup_logging(enable_console=True)
logger = get_logger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="WhatsApp AI Backend",
    description="Advanced WhatsApp AI chat system with Ollama integration",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[settings.app_host, "localhost", "127.0.0.1"]
    )

# Add custom middleware (order matters - last added is executed first)
app.add_middleware(LoggingMiddleware)

# Add rate limiting middleware
from .middleware.rate_limit import rate_limit_middleware
app.middleware("http")(rate_limit_middleware)


# Exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation Error",
            "message": str(exc),
            "error_code": getattr(exc, "error_code", "VALIDATION_ERROR"),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(WhatsAppAPIError)
async def whatsapp_api_exception_handler(request: Request, exc: WhatsAppAPIError):
    """Handle WhatsApp API errors"""
    logger.error(f"WhatsApp API error: {str(exc)}")
    return JSONResponse(
        status_code=502,
        content={
            "error": "WhatsApp API Error",
            "message": "Failed to communicate with WhatsApp API",
            "error_code": getattr(exc, "error_code", "WHATSAPP_API_ERROR"),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(OllamaError)
async def ollama_exception_handler(request: Request, exc: OllamaError):
    """Handle Ollama errors"""
    logger.error(f"Ollama error: {str(exc)}")
    return JSONResponse(
        status_code=503,
        content={
            "error": "AI Service Error",
            "message": "Failed to generate AI response",
            "error_code": getattr(exc, "error_code", "OLLAMA_ERROR"),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(ChatHistoryError)
async def chat_history_exception_handler(request: Request, exc: ChatHistoryError):
    """Handle chat history errors"""
    logger.error(f"Chat history error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Chat History Error",
            "message": "Failed to process chat history",
            "error_code": getattr(exc, "error_code", "CHAT_HISTORY_ERROR"),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(ServiceUnavailableError)
async def service_unavailable_exception_handler(request: Request, exc: ServiceUnavailableError):
    """Handle service unavailable errors"""
    logger.error(f"Service unavailable: {str(exc)}")
    return JSONResponse(
        status_code=503,
        content={
            "error": "Service Unavailable",
            "message": "Required service is temporarily unavailable",
            "error_code": getattr(exc, "error_code", "SERVICE_UNAVAILABLE"),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(WhatsAppAIException)
async def general_exception_handler(request: Request, exc: WhatsAppAIException):
    """Handle general application errors"""
    logger.error(f"Application error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "error_code": getattr(exc, "error_code", "INTERNAL_ERROR"),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "error_code": "UNEXPECTED_ERROR",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting WhatsApp AI Backend...")
    
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Start SIP server
        try:
            from .services.sip_service import sip_service
            from .core.config import get_settings
            settings = get_settings()
            await sip_service.start_sip_server(
                host=settings.sip_server_host,
                port=settings.sip_server_port
            )
            logger.info(f"SIP server started on {settings.sip_server_host}:{settings.sip_server_port}")
        except Exception as e:
            logger.warning(f"Could not start SIP server: {str(e)} - continuing without it")
        
        # Check Ollama service health (non-blocking)
        # Temporarily disabled to allow backend to start
        # try:
        #     from .services.ollama_service import OllamaService
        #     ollama_service = OllamaService()
        #     
        #     if ollama_service.check_health():
        #         logger.info("Ollama service is healthy")
        #     else:
        #         logger.warning("Ollama service is not available - continuing without it")
        # except Exception as e:
        #     logger.warning(f"Could not check Ollama service: {str(e)} - continuing without it")
        logger.info("Ollama service check disabled - continuing without verification")
        
        logger.info("WhatsApp AI Backend started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down WhatsApp AI Backend...")
    
    try:
        # Stop SIP server
        try:
            from .services.sip_service import sip_service
            await sip_service.stop_sip_server()
            logger.info("SIP server stopped")
        except Exception as e:
            logger.warning(f"Error stopping SIP server: {str(e)}")
        
        # Close database connections
        close_db()
        logger.info("Database connections closed")
        
        logger.info("WhatsApp AI Backend shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Application health check"""
    try:
        # Check database connection
        from .core.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            db_status = "connected"
        finally:
            db.close()
        
        # Check Ollama service
        try:
            from .services.ollama_service import OllamaService
            ollama_service = OllamaService()
            ollama_healthy = ollama_service.check_health()
        except Exception as e:
            logger.warning(f"Could not check Ollama service: {str(e)}")
            ollama_healthy = False
        
        return {
            "status": "healthy",
            "version": "1.0.0",
            "database": db_status,
            "ollama": "healthy" if ollama_healthy else "unavailable",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "WhatsApp AI Backend",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
        "health": "/health"
    }


# Mount static files for TTS audio
tts_directory = "storage/media/tts"
os.makedirs(tts_directory, exist_ok=True)
app.mount("/static/tts", StaticFiles(directory=tts_directory), name="tts")

# Include API routes
app.include_router(
    api_router,
    prefix="/api/v1"
)