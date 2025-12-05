"""
Health check endpoints for monitoring system status
"""
import psutil
import shutil
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import httpx

from app.core.database import get_db
from app.core.config import get_settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


@router.get("/")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "Eva AI Assistant"}


@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with all services"""
    checks = {
        "database": await check_database(db),
        "ollama": await check_ollama(),
        "disk_space": check_disk_space(),
        "memory": check_memory()
    }
    
    # Overall status
    all_healthy = all(check.get("status") == "healthy" for check in checks.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks
    }


async def check_database(db: Session) -> Dict[str, Any]:
    """Check database connectivity"""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }


async def check_ollama() -> Dict[str, Any]:
    """Check Ollama service status"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {
                    "status": "healthy",
                    "message": "Ollama is running",
                    "models_count": len(models)
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": f"Ollama returned status {response.status_code}"
                }
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Cannot connect to Ollama: {str(e)}"
        }


def check_disk_space() -> Dict[str, Any]:
    """Check available disk space"""
    try:
        total, used, free = shutil.disk_usage("/")
        free_gb = free // (2**30)
        total_gb = total // (2**30)
        usage_percent = (used / total) * 100
        
        status = "healthy"
        if free_gb < 1:  # Less than 1GB free
            status = "critical"
        elif free_gb < 5:  # Less than 5GB free
            status = "warning"
        
        return {
            "status": status,
            "free_gb": free_gb,
            "total_gb": total_gb,
            "usage_percent": round(usage_percent, 2)
        }
    except Exception as e:
        logger.error(f"Disk space check failed: {e}")
        return {
            "status": "unknown",
            "message": str(e)
        }


def check_memory() -> Dict[str, Any]:
    """Check memory usage"""
    try:
        memory = psutil.virtual_memory()
        
        status = "healthy"
        if memory.percent > 95:
            status = "critical"
        elif memory.percent > 85:
            status = "warning"
        
        return {
            "status": status,
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "usage_percent": memory.percent
        }
    except Exception as e:
        logger.error(f"Memory check failed: {e}")
        return {
            "status": "unknown",
            "message": str(e)
        }


@router.get("/services/kanitts")
async def check_kanitts():
    """Check KaniTTS service status"""
    try:
        kanitts_host = getattr(settings, 'kanitts_host', 'localhost')
        kanitts_port = getattr(settings, 'kanitts_port', 5002)
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://{kanitts_host}:{kanitts_port}/health")
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "service": "KaniTTS",
                    "message": "KaniTTS is running"
                }
            else:
                return {
                    "status": "unhealthy",
                    "service": "KaniTTS",
                    "message": f"KaniTTS returned status {response.status_code}"
                }
    except Exception as e:
        return {
            "status": "unavailable",
            "service": "KaniTTS",
            "message": f"Cannot connect to KaniTTS: {str(e)}"
        }


@router.get("/services/twilio")
async def check_twilio():
    """Check Twilio configuration"""
    twilio_sid = getattr(settings, 'twilio_account_sid', None)
    twilio_token = getattr(settings, 'twilio_auth_token', None)
    
    if twilio_sid and twilio_token:
        return {
            "status": "configured",
            "service": "Twilio",
            "message": "Twilio credentials are configured"
        }
    else:
        return {
            "status": "not_configured",
            "service": "Twilio",
            "message": "Twilio credentials not configured"
        }


@router.get("/services/whatsapp")
async def check_whatsapp():
    """Check WhatsApp configuration"""
    wa_token = getattr(settings, 'whatsapp_access_token', None)
    wa_phone_id = getattr(settings, 'whatsapp_phone_number_id', None)
    
    if wa_token and wa_phone_id:
        return {
            "status": "configured",
            "service": "WhatsApp",
            "message": "WhatsApp credentials are configured"
        }
    else:
        return {
            "status": "not_configured",
            "service": "WhatsApp",
            "message": "WhatsApp credentials not configured"
        }
