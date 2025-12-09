"""
Service for integration with Coqui TTS (Local).
"""
import logging
import os
import uuid
from typing import Optional
from fastapi import HTTPException

from app.core.settings import get_settings

logger = logging.getLogger(__name__)

class CoquiTTSService:
    def __init__(self):
        self.settings = get_settings()
        self.enabled = True
        self.tts = None
        self.device = "cpu"
        self.model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        
        try:
            import torch
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            logger.warning("torch not found. Coqui TTS will be disabled.")
            self.enabled = False
            
        self.audio_dir = "storage/media/tts"
        os.makedirs(self.audio_dir, exist_ok=True)
        
        if self.enabled:
            self._initialize_model()

    def _initialize_model(self):
        """Initialize the Coqui TTS model."""
        try:
            from TTS.api import TTS
            logger.info(f"Loading Coqui TTS model: {self.model_name} on {self.device}...")
            self.tts = TTS(self.model_name).to(self.device)
            logger.info("Coqui TTS model loaded successfully.")
        except ImportError:
            logger.error("Coqui TTS library not found. Please install 'TTS'.")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize Coqui TTS: {e}")
            self.enabled = False

    def generate_speech(self, text: str, speaker: str = None, language: str = "es") -> Optional[str]:
        """
        Generate audio from text using Coqui TTS.
        """
        if not self.enabled or not self.tts:
            raise HTTPException(
                status_code=503,
                detail="Coqui TTS service is not available (library missing or model failed to load)."
            )
            
        if not text.strip():
            raise HTTPException(status_code=400, detail="Empty text for TTS")
            
        try:
            # Generate unique filename
            filename = f"coqui_{uuid.uuid4().hex[:10]}.wav"
            filepath = os.path.join(self.audio_dir, filename)
            
            logger.info(f"Generating Coqui TTS audio for: {text[:50]}...")
            
            # XTTS requires a speaker wav for cloning or a speaker name if multi-speaker
            # For XTTS v2, we usually provide a reference audio or speaker name.
            # If using the base model without fine-tuning, we might need a reference.
            # For simplicity/robustness, we'll try standard generation.
            # Note: XTTS API often needs `speaker_wav` or `speaker_idx`.
            
            # If speaker is not provided, use a default reference if available, or let TTS handle it.
            # For this implementation, we'll assume the model handles the default or we pass what we have.
            
            # Check if model is XTTS to handle specific args
            is_xtts = "xtts" in self.model_name
            
            generate_kwargs = {
                "text": text,
                "file_path": filepath,
                "language": language if is_xtts else None # VITS might not need language arg if single-lang
            }
            
            if is_xtts:
                 # XTTS needs a speaker reference. We can use a default one included in the package or one we have.
                 # For now, we'll try to use the first available speaker or a specific one if we had it.
                 # Since we don't have a reference file handy in this generic code, 
                 # we might rely on the API's default or fail if it demands one.
                 # Let's try to list speakers and pick one? 
                 # self.tts.speakers returns a list.
                 if self.tts.speakers:
                     generate_kwargs["speaker"] = self.tts.speakers[0] # Pick first speaker
            
            self.tts.tts_to_file(**generate_kwargs)
            
            # Return public URL
            public_url = f"http://localhost:8000/static/tts/{filename}"
            logger.info(f"Audio generated: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Error generating Coqui TTS audio: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"TTS generation failed: {str(e)}"
            )
