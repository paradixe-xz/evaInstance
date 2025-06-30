"""
Configuración para el TTS mejorado
"""

import os

# Configuración de TTS
TTS_METHOD = os.getenv('TTS_METHOD', 'gtts_improved')

# Opciones disponibles:
# - "gtts_improved": Google TTS con mejor configuración (requiere internet)
# - "pyttsx3": TTS offline usando voces del sistema (no requiere internet)

def get_tts_info():
    """Obtiene información sobre el método de TTS configurado"""
    if TTS_METHOD == "gtts_improved":
        return {
            "method": "Google TTS Mejorado",
            "requires_internet": True,
            "language": "Español",
            "quality": "Buena",
            "speed": "Normal"
        }
    elif TTS_METHOD == "pyttsx3":
        return {
            "method": "TTS Offline (pyttsx3)",
            "requires_internet": False,
            "language": "Depende de voces del sistema",
            "quality": "Variable",
            "speed": "Configurable"
        }
    else:
        return {
            "method": "Desconocido",
            "requires_internet": True,
            "language": "Español",
            "quality": "Básica",
            "speed": "Normal"
        }

def print_tts_status():
    """Imprime el estado actual del TTS"""
    info = get_tts_info()
    print("🎤 Configuración de TTS:")
    print(f"   Método: {info['method']}")
    print(f"   Requiere internet: {'Sí' if info['requires_internet'] else 'No'}")
    print(f"   Idioma: {info['language']}")
    print(f"   Calidad: {info['quality']}")
    print(f"   Velocidad: {info['speed']}")

if __name__ == "__main__":
    print_tts_status() 