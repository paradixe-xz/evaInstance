"""
Endpoints para manejo de llamadas telefónicas
"""
from fastapi import APIRouter, HTTPException, Form, Request, UploadFile, File
from fastapi.responses import Response, JSONResponse
from typing import Optional
import logging
import tempfile
import os
from pydantic import BaseModel

from app.services.call_service import CallService
from app.services.stt_service import STTService
from app.services.coqui_service import CoquiTTSService
from twilio.twiml.voice_response import VoiceResponse

logger = logging.getLogger(__name__)

router = APIRouter()
call_service = CallService()
stt_service = STTService()

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

# Modelos Pydantic para la interfaz web
class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "es-ES-ElviraNeural"
    speed: Optional[float] = 1.0

class ConversationRequest(BaseModel):
    phone_number: str
    initial_message: Optional[str] = None

class SpeechProcessRequest(BaseModel):
    conversation_id: str
    transcript: str

# === ENDPOINTS PARA INTERFAZ WEB ===

@router.post("/tts/generate")
async def generate_tts_web(request: TTSRequest):
    """Generar audio TTS para la interfaz web"""
    try:
        logger.info(f"Generando TTS web: {request.text[:50]}...")
        # Pre-chequear disponibilidad
        # if not call_service.kanitts_service.is_available():
        #     raise HTTPException(status_code=503, detail="KaniTTS no disponible")
        
        # Generar audio usando Coqui TTS (Local)
        tts_service = CoquiTTSService()
        audio_file = tts_service.generate_speech(
            text=request.text,
            speaker=request.voice # Pass voice as speaker
        )
        
        if audio_file:
            # Construir URL pública para el archivo de audio
            filename = os.path.basename(audio_file)
            audio_url = f"http://localhost:8000/static/tts/{filename}"
            
            return {
                "success": True,
                "audio_url": audio_url,
                "filename": filename,
                "text": request.text
            }
        else:
            # Esto no debería pasar con el nuevo manejo de errores
            raise HTTPException(status_code=500, detail="Error inesperado: servicio TTS devolvió None")
            
    except HTTPException:
        # Re-lanzar HTTPExceptions tal como están
        raise
    except Exception as e:
        logger.error(f"Error en TTS web: {e}")
        # Determinar el código de estado basado en el tipo de error
        if "modo de prueba" in str(e).lower() or "no inicializado" in str(e).lower():
            status_code = 503  # Service Unavailable
        elif "timeout" in str(e).lower() or "conectar" in str(e).lower():
            status_code = 502  # Bad Gateway
        else:
            status_code = 500  # Internal Server Error
            
        raise HTTPException(status_code=status_code, detail=str(e))

@router.post("/stt/transcribe")
async def transcribe_audio_web(audio: UploadFile = File(...)):
    """Transcribir audio a texto para la interfaz web"""
    try:
        logger.info(f"Transcribiendo audio web: {audio.filename}")
        
        # Guardar archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Transcribir audio usando el servicio STT
            transcript = stt_service.transcribe_audio_data(content, language="es-ES")
            
            if transcript:
                return {
                    "success": True,
                    "transcript": transcript,
                    "filename": audio.filename
                }
            else:
                return {
                    "success": False,
                    "transcript": "No se pudo transcribir el audio",
                    "filename": audio.filename
                }
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"Error en STT web: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kanitts/status")
async def kanitts_status():
    """Verificar estado del servicio KaniTTS"""
    try:
        available = call_service.kanitts_service.is_available()
        return {
            "available": available,
            "status": "online" if available else "offline"
        }
    except Exception as e:
        logger.error(f"Error verificando KaniTTS: {e}")
        return {
            "available": False,
            "status": "error",
            "error": str(e)
        }

@router.get("/tts/status")
async def tts_status():
    """Verificar estado del servicio TTS actual (CoquiTTS)"""
    try:
        # Instanciar servicio para verificar
        # En una implementación ideal, esto sería un singleton inyectado
        tts_service = CoquiTTSService()
        available = tts_service.enabled and tts_service.tts is not None
        
        return {
            "available": available,
            "status": "online" if available else "offline",
            "provider": "coqui-tts"
        }
    except Exception as e:
        logger.error(f"Error verificando TTS: {e}")
        return {
            "available": False,
            "status": "error",
            "error": str(e)
        }

@router.post("/start-conversation")
async def start_conversation_web(request: ConversationRequest):
    """Iniciar conversación para la interfaz web"""
    try:
        logger.info(f"Iniciando conversación web para {request.phone_number}")
        
        # Generar ID único para la conversación
        import uuid
        conversation_id = str(uuid.uuid4())
        
        # Mensaje inicial por defecto
        initial_message = request.initial_message or "Hola, soy Eva, tu asistente de inteligencia artificial. ¿En qué puedo ayudarte hoy?"
        
        # Simular inicio de conversación (en una implementación real, aquí iniciarías la llamada)
        return {
            "success": True,
            "conversation_id": conversation_id,
            "phone_number": request.phone_number,
            "initial_message": initial_message,
            "status": "active"
        }
        
    except Exception as e:
        logger.error(f"Error iniciando conversación web: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-speech")
async def process_speech_web(request: SpeechProcessRequest):
    """Procesar entrada de voz en conversación web"""
    try:
        logger.info(f"Procesando voz web: {request.transcript}")
        
        # Aquí integrarías con el servicio de chat para generar respuesta
        # Por ahora, simulamos una respuesta
        response_text = f"Entiendo que dijiste: '{request.transcript}'. ¿En qué más puedo ayudarte?"
        
        return {
            "success": True,
            "conversation_id": request.conversation_id,
            "user_input": request.transcript,
            "response": response_text
        }
        
    except Exception as e:
        logger.error(f"Error procesando voz web: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/end-conversation/{conversation_id}")
async def end_conversation_web(conversation_id: str):
    """Finalizar conversación web"""
    try:
        logger.info(f"Finalizando conversación web: {conversation_id}")
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "message": "Conversación finalizada correctamente"
        }
        
    except Exception as e:
        logger.error(f"Error finalizando conversación web: {e}")
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