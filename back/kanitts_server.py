#!/usr/bin/env python3
"""Servidor KaniTTS simplificado para el puerto 8020."""

import io
import asyncio
import logging
import tempfile
import sys
import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kani TTS API", description="Text-to-Speech API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TTSRequest(BaseModel):
    text: str
    temperature: Optional[float] = 0.6
    max_tokens: Optional[int] = 1200

# Variable global para el sistema TTS
tts_system = None
tts_initialized = False

@app.on_event("startup")
async def startup_event():
    """Inicializar sistema TTS al arrancar."""
    global tts_system, tts_initialized
    try:
        logger.info("Intentando inicializar sistema TTS...")
        
        # Agregar el directorio kani-tts al path
        kani_tts_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kani-tts")
        if os.path.exists(kani_tts_path):
            sys.path.insert(0, kani_tts_path)
            logger.info(f"Agregado {kani_tts_path} al path")
        

        try:
            from kanitts import Config, TTSFactory, ModelConfig, AudioConfig, TokenRegistry
            logger.info("Módulos KaniTTS importados exitosamente")
            
            # Configuración personalizada para mejorar la fluidez del habla
            model_config = ModelConfig(
                model_name='nineninesix/kani-tts-450m-0.1-pt',
                device_map="auto",
                torch_dtype="bfloat16",
                max_new_tokens=1500,  # Aumentado para permitir frases más largas
                temperature=0.8,      # Reducido para más consistencia
                top_p=0.9,           # Reducido para más coherencia
                repetition_penalty=1.05  # Reducido para menos repetición
            )
            
            audio_config = AudioConfig(
                nemo_model_name="nvidia/nemo-nano-codec-22khz-0.6kbps-12.5fps",
                sample_rate=22050,
                device=None
            )
            
            config = Config(
                model=model_config,
                audio=audio_config,
                tokens=TokenRegistry()
            )
            
            tts_system, _ = TTSFactory.create_system(config)
            
            logger.info("Calentando modelo TTS...")
            await asyncio.to_thread(tts_system.run_model, "Frase de calentamiento para inicialización TTS.")
            logger.info("Calentamiento del modelo TTS completado")
            
            tts_initialized = True
            logger.info("✅ Sistema TTS inicializado exitosamente")
            
        except ImportError as e:
            logger.warning(f"No se pudo importar KaniTTS: {e}")
            logger.info("Funcionando en modo de prueba sin TTS real")
            tts_initialized = False
        except Exception as e:
            logger.error(f"Error al inicializar TTS: {e}")
            logger.info("Funcionando en modo de prueba sin TTS real")
            tts_initialized = False
            
    except Exception as e:
        logger.error(f"Error general en startup: {e}")
        tts_initialized = False

@app.get("/")
async def root():
    """Endpoint raíz con información de la API."""
    return {
        "message": "Kani TTS API",
        "status": "disponible" if tts_initialized else "modo de prueba",
        "endpoints": {
            "/tts": "POST - Generar voz desde texto",
            "/health": "GET - Verificación de salud"
        }
    }

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud."""
    return {
        "status": "healthy", 
        "tts_initialized": tts_initialized,
        "mode": "full" if tts_initialized else "test"
    }

@app.post("/synthesize")
async def synthesize_speech(request: dict):
    """Endpoint de síntesis compatible con el servicio KaniTTS."""
    text = request.get("text", "")
    speaker = request.get("speaker", "default")
    language = request.get("language", "es")
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="Texto requerido")
    
    return await generate_speech_internal(text)

@app.post("/tts")
async def generate_speech(request: TTSRequest):
    """Generar voz desde texto y devolver audio WAV."""
    return await generate_speech_internal(request.text)

async def generate_speech_internal(text: str):
    if not tts_initialized:
        # Modo de prueba - devolver un archivo de audio de prueba
        logger.info(f"Modo de prueba - generando respuesta para: {text[:50]}...")
        
        # Crear un archivo WAV de prueba simple (silencio)
        import numpy as np
        try:
            import soundfile as sf
        except ImportError:
            # Si no tenemos soundfile, crear un WAV básico manualmente
            sample_rate = 22050
            duration = 2  # 2 segundos
            samples = int(sample_rate * duration)
            audio_data = np.zeros(samples, dtype=np.float32)
            
            # Crear WAV header manualmente
            import struct
            wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
                b'RIFF', 36 + samples * 2, b'WAVE', b'fmt ', 16, 1, 1, 
                sample_rate, sample_rate * 2, 2, 16, b'data', samples * 2)
            
            # Convertir a 16-bit PCM
            audio_16bit = (audio_data * 32767).astype(np.int16)
            wav_data = wav_header + audio_16bit.tobytes()
            
            return StreamingResponse(
                io.BytesIO(wav_data),
                media_type="audio/wav",
                headers={
                    "Content-Disposition": "inline; filename=test_speech.wav",
                    "Cache-Control": "no-cache"
                }
            )
    
    if not tts_system:
        raise HTTPException(status_code=503, detail="Sistema TTS no inicializado")
    
    try:
        logger.info(f"Generando voz para texto: {text[:50]}...")
        
        audio, _ = tts_system.run_model(text)
        
        # Convertir array numpy a bytes WAV usando scipy
        import numpy as np
        from scipy.io import wavfile
        import io
        
        # Asegurar que el audio esté en el formato correcto
        if audio.dtype != np.int16:
            # Normalizar y convertir a int16
            audio_normalized = np.clip(audio, -1.0, 1.0)
            audio_int16 = (audio_normalized * 32767).astype(np.int16)
        else:
            audio_int16 = audio
        
        # Crear archivo WAV en memoria
        wav_buffer = io.BytesIO()
        wavfile.write(wav_buffer, 22050, audio_int16)
        wav_data = wav_buffer.getvalue()
        
        return StreamingResponse(
            io.BytesIO(wav_data),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "inline; filename=generated_speech.wav",
                "Cache-Control": "no-cache"
            }
        )
        
    except Exception as e:
        logger.error(f"Error generando voz: {e}")
        raise HTTPException(status_code=500, detail=f"Falló la generación de voz: {str(e)}")

if __name__ == "__main__":
    logger.info("Iniciando servidor KaniTTS en puerto 8020...")
    uvicorn.run(app, host="0.0.0.0", port=8020, log_level="info")