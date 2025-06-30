# evaInstance

Sistema de IA conversacional con TTS mejorado en español.

## Características
- Integración con Ollama para respuestas de IA
- Text-to-Speech mejorado en español
- Soporte para llamadas telefónicas y WhatsApp
- Múltiples opciones de TTS (online y offline)

## TTS Mejorado

El sistema incluye dos opciones de Text-to-Speech:

### 1. Google TTS Mejorado (gtts_improved)
- Requiere conexión a internet
- Buena calidad de voz en español
- Configuración optimizada

### 2. TTS Offline (pyttsx3)
- No requiere internet
- Usa voces del sistema operativo
- Funciona sin conexión

## Configuración

Para cambiar el método de TTS, establece la variable de entorno:
```bash
export TTS_METHOD=gtts_improved  # o pyttsx3
```

## Requirements:
- fastapi
- pydantic
- twilio
- speechrecognition
- gtts
- pygame
- ollama
- pyttsx3

See requirements.txt for installation.
