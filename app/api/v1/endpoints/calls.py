"""
Endpoints para manejo de llamadas telefónicas
"""
from fastapi import APIRouter, HTTPException, Form, Request
from fastapi.responses import Response
from typing import Optional
import logging

from app.services.call_service import CallService
from twilio.twiml.voice_response import VoiceResponse

logger = logging.getLogger(__name__)

router = APIRouter()
call_service = CallService()

@router.post("/make-call")
async def make_call(
    to_number: str,
    message: str
):
    """Realizar llamada saliente con mensaje"""
    try:
        result = call_service.make_call(to_number, message)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error en make_call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/incoming")
async def handle_incoming_call(request: Request):
    """Webhook para llamadas entrantes"""
    try:
        # Obtener datos del webhook de Twilio
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        from_number = form_data.get("From")
        
        logger.info(f"Llamada entrante de {from_number}, SID: {call_sid}")
        
        # Crear respuesta TwiML
        message = "¡Hola! Gracias por llamar. Este es un mensaje automatizado."
        twiml = call_service.create_simple_twiml(message)
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error manejando llamada entrante: {e}")
        response = VoiceResponse()
        response.say("Lo siento, hay un problema técnico.", language='es-MX')
        return Response(content=str(response), media_type="application/xml")

@router.post("/webhook/speech")
async def handle_speech_input(
    CallSid: str = Form(...),
    SpeechResult: Optional[str] = Form(None)
):
    """Webhook para procesar entrada de voz del usuario"""
    try:
        if not SpeechResult:
            logger.warning(f"No se recibió entrada de voz para call {CallSid}")
            response = VoiceResponse()
            response.say("No escuché nada. Por favor, intenta de nuevo.", language='es-MX')
            response.hangup()
            return Response(content=str(response), media_type="application/xml")
        
        logger.info(f"Procesando voz de {CallSid}: {SpeechResult}")
        
        # Procesar entrada de voz y generar respuesta
        twiml = call_service.process_speech_input(CallSid, SpeechResult)
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error procesando entrada de voz: {e}")
        response = VoiceResponse()
        response.say("Lo siento, hubo un error procesando tu solicitud.", language='es-MX')
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

@router.post("/start-conversation")
async def start_conversation_call(
    to_number: str,
    welcome_message: Optional[str] = None
):
    """Iniciar llamada conversacional con IA"""
    try:
        if not welcome_message:
            welcome_message = "¡Hola! Soy tu asistente virtual. ¿En qué puedo ayudarte hoy?"
        
        result = call_service.start_conversation_call(to_number, welcome_message)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error iniciando conversación: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation/{call_sid}")
async def get_conversation_history(call_sid: str):
    """Obtener historial de conversación"""
    try:
        history = call_service.get_conversation_history(call_sid)
        return {
            "success": True,
            "call_sid": call_sid,
            "conversation": history
        }
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/end-conversation/{call_sid}")
async def end_conversation(call_sid: str):
    """Finalizar conversación"""
    try:
        success = call_service.end_conversation(call_sid)
        return {
            "success": success,
            "message": "Conversación finalizada" if success else "Conversación no encontrada"
        }
    except Exception as e:
        logger.error(f"Error finalizando conversación: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Verificar estado del servicio de llamadas"""
    try:
        # Verificar servicios dependientes
        kanitts_available = call_service.kanitts_service.is_available()
        twilio_configured = call_service.twilio_client is not None
        
        return {
            "status": "healthy",
            "services": {
                "kanitts": "available" if kanitts_available else "unavailable",
                "twilio": "configured" if twilio_configured else "not_configured"
            }
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))