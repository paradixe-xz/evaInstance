"""
Servicio para integración con KaniTTS (Text-to-Speech)
"""
import logging
import requests
import os
import uuid
from typing import Optional
from urllib.parse import urljoin
from fastapi import HTTPException

from app.core.settings import get_settings

logger = logging.getLogger(__name__)

class KaniTTSService:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = getattr(self.settings, 'KANITTS_BASE_URL', 'http://localhost:8020')
        self.default_speaker = getattr(self.settings, 'KANITTS_DEFAULT_SPEAKER', 'es-mx-female-1')
        self.default_language = getattr(self.settings, 'KANITTS_DEFAULT_LANGUAGE', 'es')
        self.timeout = getattr(self.settings, 'KANITTS_TIMEOUT', 120)
        self.enabled = getattr(self.settings, 'KANITTS_ENABLED', True)
        
        # Directorio para almacenar archivos de audio
        self.audio_dir = "storage/media/tts"
        os.makedirs(self.audio_dir, exist_ok=True)

    def is_available(self) -> bool:
        """Verificar si KaniTTS está disponible"""
        if not self.enabled:
            return False
            
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"KaniTTS no disponible: {e}")
            return False

    def generate_speech(self, text: str, speaker: str = None, language: str = None) -> Optional[str]:
        """
        Generar audio a partir de texto usando KaniTTS
        
        Args:
            text: Texto a convertir a voz
            speaker: Voz a utilizar (opcional)
            language: Idioma (opcional)
            
        Returns:
            URL del archivo de audio generado
            
        Raises:
            HTTPException: Si hay errores en el servicio TTS
        """
        if not self.enabled:
            raise HTTPException(
                status_code=503,
                detail="Servicio TTS deshabilitado"
            )
            
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Texto vacío para TTS"
            )
            
        try:
            # Parámetros para la solicitud
            speaker = speaker or self.default_speaker
            language = language or self.default_language
            
            # Datos para la API
            payload = {
                "text": text,
                "speaker": speaker,
                "language": language
            }
            
            # Realizar solicitud a KaniTTS
            response = requests.post(
                f"{self.base_url}/synthesize",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                # Generar nombre único para el archivo
                filename = f"call_tts_{uuid.uuid4().hex[:10]}.wav"
                filepath = os.path.join(self.audio_dir, filename)
                
                # Guardar archivo de audio
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # Retornar URL pública del archivo
                public_url = f"http://localhost:8000/static/tts/{filename}"
                logger.info(f"Audio generado: {public_url}")
                return public_url
                
            elif response.status_code == 503:
                # Servidor en modo de prueba
                raise HTTPException(
                    status_code=503,
                    detail="Servicio TTS en modo de prueba - sistema no inicializado"
                )
            else:
                logger.error(f"Error en KaniTTS: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Error del servidor TTS: {response.status_code}"
                )
                
        except requests.exceptions.Timeout:
            logger.error("Timeout en solicitud a KaniTTS")
            raise HTTPException(
                status_code=504,
                detail="Timeout en servicio TTS"
            )
        except requests.exceptions.ConnectionError:
            logger.error("Error de conexión con KaniTTS")
            raise HTTPException(
                status_code=502,
                detail="No se puede conectar al servicio TTS"
            )
        except HTTPException:
            # Re-lanzar HTTPExceptions
            raise
        except Exception as e:
            logger.error(f"Error inesperado en KaniTTS: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error interno del servicio TTS: {str(e)}"
            )

    def get_available_speakers(self) -> list:
        """Obtener lista de voces disponibles"""
        if not self.enabled:
            return []
            
        try:
            response = requests.get(
                f"{self.base_url}/speakers",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('speakers', [])
            else:
                logger.error(f"Error obteniendo voces: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error obteniendo voces disponibles: {e}")
            return []

    def get_supported_languages(self) -> list:
        """Obtener lista de idiomas soportados"""
        if not self.enabled:
            return []
            
        try:
            response = requests.get(
                f"{self.base_url}/languages",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('languages', [])
            else:
                logger.error(f"Error obteniendo idiomas: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error obteniendo idiomas soportados: {e}")
            return []

    def cleanup_old_files(self, max_age_hours: int = 24):
        """Limpiar archivos de audio antiguos"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.audio_dir):
                if filename.endswith('.wav'):
                    filepath = os.path.join(self.audio_dir, filename)
                    file_age = current_time - os.path.getctime(filepath)
                    
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        logger.info(f"Archivo eliminado: {filename}")
                        
        except Exception as e:
            logger.error(f"Error limpiando archivos antiguos: {e}")