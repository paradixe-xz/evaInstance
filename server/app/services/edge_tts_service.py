"""
Service for integration with Edge-TTS (Microsoft Edge's online Text-to-Speech).
Provides high-quality neural voices for free.
"""
import logging
import os
import uuid
import asyncio
import nest_asyncio
from typing import Optional, List
from fastapi import HTTPException
import edge_tts

from app.core.settings import get_settings

# Apply nest_asyncio to allow nested event loops (required for running edge-tts in FastAPI)
nest_asyncio.apply()

logger = logging.getLogger(__name__)

class EdgeTTSService:
    def __init__(self):
        self.settings = get_settings()
        # Default to a high-quality Mexican Spanish voice
        self.default_voice = "es-MX-DaliaNeural" 
        self.audio_dir = "storage/media/tts"
        os.makedirs(self.audio_dir, exist_ok=True)

    async def generate_speech(self, text: str, voice: str = None) -> Optional[str]:
        """
        Generate audio from text using Edge-TTS.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (optional, defaults to es-MX-DaliaNeural)
            
        Returns:
            URL of the generated audio file
        """
        if not text.strip():
            raise HTTPException(status_code=400, detail="Empty text for TTS")
            
        try:
            voice = voice or self.default_voice
            
            # Generate unique filename
            filename = f"tts_{uuid.uuid4().hex[:10]}.mp3"
            filepath = os.path.join(self.audio_dir, filename)
            
            logger.info(f"Generating Edge-TTS audio with voice {voice}...")
            
            # Create communicate object
            communicate = edge_tts.Communicate(text, voice)
            
            # Save to file
            await communicate.save(filepath)
            
            # Return public URL
            # Assuming static files are served from /static/tts
            public_url = f"http://localhost:8000/static/tts/{filename}"
            logger.info(f"Audio generated successfully: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Error generating Edge-TTS audio: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"TTS generation failed: {str(e)}"
            )

    async def get_available_voices(self, language: str = "es") -> List[dict]:
        """Get available voices, optionally filtered by language."""
        try:
            voices = await edge_tts.list_voices()
            
            if language:
                return [v for v in voices if v["ShortName"].startswith(language)]
            return voices
            
        except Exception as e:
            logger.error(f"Error listing voices: {e}")
            return []
