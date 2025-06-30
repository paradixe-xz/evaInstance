# evaInstance

Sistema de IA conversacional con TTS mejorado en español y procesamiento de archivos Excel.

## Características
- Integración con Ollama para respuestas de IA
- Text-to-Speech mejorado con ElevenLabs
- Soporte para llamadas telefónicas y WhatsApp
- Procesamiento de archivos Excel para envío masivo de contactos
- Múltiples opciones de TTS (online y offline)

## TTS Mejorado

El sistema incluye opciones de Text-to-Speech:

### 1. ElevenLabs TTS (Recomendado)
- Requiere conexión a internet
- Excelente calidad de voz en español
- Configuración optimizada para Twilio
- Conversión automática a WAV 8kHz mono

### 2. Google TTS Mejorado (gtts_improved)
- Requiere conexión a internet
- Buena calidad de voz en español
- Configuración optimizada

### 3. TTS Offline (pyttsx3)
- No requiere internet
- Usa voces del sistema operativo
- Funciona sin conexión

## Procesamiento de Archivos Excel

El sistema ahora soporta el envío masivo de contactos mediante archivos Excel:

### Formato Requerido
El archivo Excel debe contener las siguientes columnas:
- **nombre**: Nombre del contacto (opcional pero recomendado)
- **numero**: Número de teléfono (requerido)

### Ejemplo de contenido:
```
nombre,numero
Juan Pérez,+34600123456
María García,34600123457
Carlos López,+34600123458
Ana Martínez,34600123459
```

### Validaciones
- Los números deben tener al menos 10 dígitos
- Se puede usar con o sin el prefijo +
- Se ignorarán las filas sin número
- Se limpian automáticamente espacios y caracteres especiales

### Funcionalidad
- Envía mensaje de WhatsApp personalizado a cada contacto
- Inicia llamada telefónica automática
- Proporciona reporte detallado del procesamiento
- Manejo de errores por contacto individual

## Configuración

### Variables de Entorno Requeridas
```bash
# Twilio
export TWILIO_ACCOUNT_SID=your_account_sid
export TWILIO_AUTH_TOKEN=your_auth_token
export TWILIO_PHONE_NUMBER=your_phone_number
export TWILIO_WHATSAPP_NUMBER=your_whatsapp_number
export TWILIO_WEBHOOK_URL=your_webhook_url

# ElevenLabs
export ELEVENLABS_API_KEY=your_api_key
export ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Rachel voice (opcional)

# URL pública para archivos de audio
export PUBLIC_BASE_URL=your_public_url
```

Para cambiar el método de TTS, establece la variable de entorno:
```bash
export TTS_METHOD=gtts_improved  # o pyttsx3
```

## Endpoints

### POST /sendNumbers
Procesa archivo Excel con contactos y envía mensajes/llamadas.

**Request:**
- Content-Type: multipart/form-data
- Body: file (archivo Excel .xlsx o .xls)

**Response:**
```json
{
  "message": "Procesamiento completado. X contactos válidos encontrados.",
  "total_contacts": 10,
  "valid_contacts": 8,
  "invalid_contacts": 2,
  "results": [...],
  "invalid_numbers": [...]
}
```

## Requirements:
- fastapi
- pydantic
- twilio
- speechrecognition
- pygame
- ollama
- python-multipart
- pydub
- elevenlabs
- pandas
- openpyxl

See requirements.txt for installation.

## Instalación

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Configurar variables de entorno

3. Ejecutar el servidor:
```bash
python main.py
```

## Uso

1. Preparar archivo Excel con columnas "nombre" y "numero"
2. Subir archivo a través del frontend o API
3. El sistema procesará automáticamente cada contacto
4. Se enviarán mensajes de WhatsApp y se iniciarán llamadas
5. Revisar el reporte de resultados
