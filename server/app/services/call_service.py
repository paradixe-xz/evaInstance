"""
Servicio para manejo de llamadas telefónicas con Twilio
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from fastapi import HTTPException

from app.core.settings import get_settings
from app.services.chat_service import ChatService
from app.services.kanitts_service import KaniTTSService

logger = logging.getLogger(__name__)

class CallService:
    def __init__(self):
        self.settings = get_settings()
        self.twilio_client = None
        self.chat_service = ChatService()
        self.kanitts_service = KaniTTSService()
        self.conversations: Dict[str, List[Dict]] = {}
        
        # Inicializar cliente Twilio si las credenciales están disponibles
        if (self.settings.twilio_account_sid and 
            self.settings.twilio_auth_token and
            self.settings.twilio_account_sid != "your-twilio-account-sid"):
            try:
                self.twilio_client = Client(
                    self.settings.twilio_account_sid,
                    self.settings.twilio_auth_token
                )
                logger.info("Cliente Twilio inicializado correctamente")
            except Exception as e:
                logger.error(f"Error inicializando cliente Twilio: {e}")
        else:
            logger.warning("Credenciales de Twilio no configuradas")

    def create_simple_twiml(self, message: str) -> str:
        """Crear respuesta TwiML simple con mensaje de voz"""
        try:
            response = VoiceResponse()
            
            # Generar audio con KaniTTS
            audio_url = self.kanitts_service.generate_speech(message)
            
            if audio_url:
                # Usar el audio generado
                response.play(audio_url)
            else:
                # Fallback a TTS de Twilio
                response.say(message, language='es-MX', voice='alice')
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Error creando TwiML: {e}")
            # Fallback básico
            response = VoiceResponse()
            response.say("Lo siento, hay un problema técnico.", language='es-MX')
            return str(response)

    def create_conversation_twiml(self, welcome_message: str = None) -> str:
        """Crear TwiML para iniciar una conversación interactiva"""
        try:
            response = VoiceResponse()
            
            # Mensaje de bienvenida
            if welcome_message:
                audio_url = self.kanitts_service.generate_speech(welcome_message)
                if audio_url:
                    response.play(audio_url)
                else:
                    response.say(welcome_message, language='es-MX', voice='alice')
            
            # Configurar captura de voz
            gather = Gather(
                input='speech',
                action='/api/v1/calls/webhook/speech',
                method='POST',
                speech_timeout='auto',
                language='es-MX'
            )
            
            gather.say("Por favor, dime en qué puedo ayudarte.", language='es-MX', voice='alice')
            response.append(gather)
            
            # Si no se detecta voz
            response.say("No escuché nada. Hasta luego.", language='es-MX', voice='alice')
            response.hangup()
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Error creando TwiML conversacional: {e}")
            response = VoiceResponse()
            response.say("Lo siento, hay un problema técnico.", language='es-MX')
            return str(response)

    def process_speech_input(self, call_sid: str, speech_result: str) -> str:
        """Procesar entrada de voz del usuario y generar respuesta"""
        try:
            # Inicializar conversación si no existe
            if call_sid not in self.conversations:
                self.conversations[call_sid] = []
            
            # Agregar mensaje del usuario
            user_message = {
                "role": "user",
                "content": speech_result,
                "timestamp": datetime.now().isoformat()
            }
            self.conversations[call_sid].append(user_message)
            
            # Generar respuesta con IA
            ai_response = self.chat_service.generate_response(
                message=speech_result,
                conversation_history=self.conversations[call_sid]
            )
            
            # Agregar respuesta de IA
            ai_message = {
                "role": "assistant", 
                "content": ai_response,
                "timestamp": datetime.now().isoformat()
            }
            self.conversations[call_sid].append(ai_message)
            
            # Crear TwiML con la respuesta
            response = VoiceResponse()
            
            # Generar audio con KaniTTS
            audio_url = self.kanitts_service.generate_speech(ai_response)
            
            if audio_url:
                response.play(audio_url)
            else:
                response.say(ai_response, language='es-MX', voice='alice')
            
            # Continuar la conversación
            gather = Gather(
                input='speech',
                action='/api/v1/calls/webhook/speech',
                method='POST',
                speech_timeout='auto',
                language='es-MX'
            )
            
            gather.say("¿Hay algo más en lo que pueda ayudarte?", language='es-MX', voice='alice')
            response.append(gather)
            
            # Si no hay más entrada
            response.say("Gracias por llamar. Hasta luego.", language='es-MX', voice='alice')
            response.hangup()
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Error procesando entrada de voz: {e}")
            response = VoiceResponse()
            response.say("Lo siento, hubo un error procesando tu solicitud.", language='es-MX')
            response.hangup()
            return str(response)

    def end_conversation(self, call_sid: str) -> bool:
        """Finalizar conversación y limpiar datos"""
        try:
            if call_sid in self.conversations:
                del self.conversations[call_sid]
                logger.info(f"Conversación {call_sid} finalizada")
                return True
            return False
        except Exception as e:
            logger.error(f"Error finalizando conversación: {e}")
            return False

    def get_conversation_history(self, call_sid: str) -> List[Dict]:
        """Obtener historial de conversación"""
        return self.conversations.get(call_sid, [])

    def make_call(self, to_number: str, message: str) -> Dict:
        """Realizar llamada saliente"""
        if not self.twilio_client:
            raise HTTPException(status_code=500, detail="Cliente Twilio no configurado")
        
        try:
            # Crear TwiML para la llamada
            twiml = self.create_simple_twiml(message)
            
            # Realizar llamada
            call = self.twilio_client.calls.create(
                twiml=twiml,
                to=to_number,
                from_=self.settings.twilio_phone_number
            )
            
            return {
                "call_sid": call.sid,
                "status": call.status,
                "to": to_number,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Error realizando llamada: {e}")
            raise HTTPException(status_code=500, detail=f"Error realizando llamada: {str(e)}")

    def start_conversation_call(self, to_number: str, welcome_message: str = None) -> Dict:
        """Iniciar llamada conversacional"""
        if not self.twilio_client:
            raise HTTPException(status_code=500, detail="Cliente Twilio no configurado")
        
        try:
            # Crear TwiML conversacional
            twiml = self.create_conversation_twiml(welcome_message)
            
            # Realizar llamada
            call = self.twilio_client.calls.create(
                twiml=twiml,
                to=to_number,
                from_=self.settings.twilio_phone_number
            )
            
            return {
                "call_sid": call.sid,
                "status": call.status,
                "to": to_number,
                "type": "conversation"
            }
            
        except Exception as e:
            logger.error(f"Error iniciando llamada conversacional: {e}")
            raise HTTPException(status_code=500, detail=f"Error iniciando llamada: {str(e)}")