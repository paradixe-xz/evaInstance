"""
Configuración para ElevenLabs TTS
"""

import os

# Configuración de ElevenLabs
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')

def get_tts_info():
    """Obtiene información sobre la configuración de ElevenLabs"""
    if ELEVENLABS_API_KEY:
        return {
            "method": "ElevenLabs TTS",
            "requires_internet": True,
            "language": "Español (Multilingüe)",
            "quality": "Premium",
            "speed": "Rápida",
            "voice_id": ELEVENLABS_VOICE_ID,
            "status": "Configurado"
        }
    else:
        return {
            "method": "ElevenLabs TTS",
            "requires_internet": True,
            "language": "Español (Multilingüe)",
            "quality": "Premium",
            "speed": "Rápida",
            "voice_id": ELEVENLABS_VOICE_ID,
            "status": "No configurado - Falta API Key"
        }

def print_tts_status():
    """Imprime el estado actual del TTS"""
    info = get_tts_info()
    print("🎤 Configuración de ElevenLabs TTS:")
    print(f"   Método: {info['method']}")
    print(f"   Requiere internet: {'Sí' if info['requires_internet'] else 'No'}")
    print(f"   Idioma: {info['language']}")
    print(f"   Calidad: {info['quality']}")
    print(f"   Velocidad: {info['speed']}")
    print(f"   Voice ID: {info['voice_id']}")
    print(f"   Estado: {info['status']}")

def get_available_voices():
    """Obtiene las voces disponibles de ElevenLabs"""
    try:
        from elevenlabs import ElevenLabs
        if ELEVENLABS_API_KEY:
            client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            available_voices = client.voices.get_all()
            return [{"id": voice.voice_id, "name": voice.name} for voice in available_voices]
        else:
            return []
    except Exception as e:
        print(f"Error obteniendo voces: {e}")
        return []

if __name__ == "__main__":
    print_tts_status()
    print("\nVoces disponibles:")
    voices = get_available_voices()
    for voice in voices[:5]:  # Mostrar solo las primeras 5
        print(f"   {voice['name']} (ID: {voice['id']})") 