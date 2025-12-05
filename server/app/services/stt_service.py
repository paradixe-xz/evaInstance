"""
Servicio para Speech-to-Text (STT)
"""
import logging
import speech_recognition as sr
import tempfile
import os
from typing import Optional
import wave
import io

logger = logging.getLogger(__name__)

class STTService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
    def transcribe_audio(self, audio_file_path: str, language: str = "es-ES") -> Optional[str]:
        """
        Transcribir audio a texto
        
        Args:
            audio_file_path: Ruta del archivo de audio
            language: Idioma para la transcripción (por defecto español)
            
        Returns:
            Texto transcrito o None si hay error
        """
        try:
            # Cargar archivo de audio
            with sr.AudioFile(audio_file_path) as source:
                # Ajustar para ruido ambiente
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # Grabar el audio
                audio_data = self.recognizer.record(source)
            
            # Transcribir usando Google Speech Recognition (gratuito)
            try:
                transcript = self.recognizer.recognize_google(audio_data, language=language)
                logger.info(f"Transcripción exitosa: {transcript[:50]}...")
                return transcript
            except sr.UnknownValueError:
                logger.warning("No se pudo entender el audio")
                return "No se pudo entender el audio"
            except sr.RequestError as e:
                logger.error(f"Error en el servicio de reconocimiento: {e}")
                return f"Error en el servicio de reconocimiento: {e}"
                
        except Exception as e:
            logger.error(f"Error transcribiendo audio: {e}")
            return None
    
    def transcribe_audio_data(self, audio_data: bytes, language: str = "es-ES") -> Optional[str]:
        """
        Transcribir datos de audio directamente
        
        Args:
            audio_data: Datos binarios del audio
            language: Idioma para la transcripción
            
        Returns:
            Texto transcrito o None si hay error
        """
        try:
            # Crear archivo temporal para speech recognition
            temp_wav_path = None
            
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                    temp_file.write(audio_data)
                    temp_wav_path = temp_file.name
                
                # Verificar si es un archivo WAV válido
                try:
                    with wave.open(temp_wav_path, 'rb') as wav_file:
                        frames = wav_file.getnframes()
                        sample_rate = wav_file.getframerate()
                        channels = wav_file.getnchannels()
                        logger.info(f"Audio info: {frames} frames, {sample_rate}Hz, {channels} channels")
                except wave.Error as e:
                    logger.error(f"WAV file error: {e}")
                    return f"Archivo de audio inválido: {e}"
                
                # Transcribir usando el archivo WAV
                return self.transcribe_audio(temp_wav_path, language)
                
            finally:
                # Limpiar archivo temporal
                if temp_wav_path and os.path.exists(temp_wav_path):
                    os.unlink(temp_wav_path)
                    
        except Exception as e:
            logger.error(f"Error transcribiendo datos de audio: {e}")
            return f"Error procesando audio: {str(e)}"