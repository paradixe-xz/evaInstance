# evaInstance

Sistema de IA conversacional con TTS mejorado en español, procesamiento de archivos Excel y programación inteligente de llamadas.

## Características
- Integración con Ollama para respuestas de IA
- Text-to-Speech mejorado con ElevenLabs
- Soporte para llamadas telefónicas y WhatsApp
- Procesamiento de archivos Excel para envío masivo de contactos
- **Sistema inteligente de formularios por WhatsApp**
- **Programación automática de llamadas con zona horaria de Barranquilla**
- **Primer contacto siempre por chat (no llamadas inmediatas)**
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

## Sistema de Formularios y Programación

### Flujo de Interacción
1. **Mensaje Inicial**: Se envía un mensaje de WhatsApp con opciones estructuradas
2. **Confirmación del Usuario**: El usuario debe confirmar si quiere recibir una llamada
3. **Programación de Llamada**: Se programa la llamada según la hora indicada por el usuario
4. **Ejecución Automática**: La llamada se ejecuta automáticamente en el momento programado

### Estados de Conversación
- **initial**: Mensaje inicial enviado, esperando respuesta
- **waiting_confirmation**: Usuario confirmó interés, esperando hora
- **scheduled_call**: Llamada programada, esperando ejecución
- **call_in_progress**: Llamada en curso
- **completed**: Conversación finalizada

### Formato de Respuestas del Usuario
El sistema reconoce múltiples formatos de tiempo:
- "Sí, llámame" - Para llamada inmediata
- "Llámame a las 3:30 PM" - Programar para hora específica
- "Mañana a las 10:00" - Programar para mañana
- "En 2 horas" - Programar en tiempo relativo
- "No, gracias" - Cerrar conversación

### Zona Horaria
- **Configurada para Barranquilla, Colombia** (UTC-5)
- Todas las programaciones se manejan en hora local
- Reconocimiento automático de horarios AM/PM y 24h

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
Procesa archivo Excel con contactos y envía mensajes iniciales de WhatsApp.

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

### GET /conversations/status
Obtiene el estado de todas las conversaciones activas.

**Response:**
```json
{
  "total_conversations": 5,
  "current_time": "2024-01-15T14:30:00-05:00",
  "timezone": "America/Bogota",
  "conversations": [
    {
      "number": "+34600123456",
      "name": "Juan Pérez",
      "stage": "scheduled_call",
      "messages_sent": 3,
      "call_scheduled": true,
      "scheduled_time": "2024-01-15T16:00:00-05:00",
      "last_interaction": "2024-01-15T14:25:00-05:00",
      "time_since_last_interaction": "0:05:00"
    }
  ]
}
```

### POST /twilio/whatsapp
Webhook para procesar mensajes de WhatsApp y manejar formularios.

### POST /twilio/voice
Webhook para manejar llamadas telefónicas programadas.

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
- pytz
- apscheduler

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

1. **Preparar archivo Excel** con columnas "nombre" y "numero"
2. **Subir archivo** a través del frontend o API
3. **El sistema envía mensajes iniciales** por WhatsApp con formularios
4. **Los usuarios responden** con sus preferencias de tiempo
5. **Las llamadas se programan automáticamente** según las respuestas
6. **Monitorear conversaciones** con el endpoint `/conversations/status`

## Scripts de Ejecución

### 🚀 Ejecutar Todo (Servidor + Monitor)
```bash
./run_server.sh
```
- Inicia el servidor principal en puerto 4000
- Inicia el monitor de estado automáticamente
- Actualiza `status.txt` cada 30 segundos
- Presiona `Ctrl+C` para detener todo

### 📊 Solo Monitor de Estado
```bash
./run_monitor.sh
```
- Útil cuando el servidor ya está corriendo
- Actualiza `status.txt` cada 30 segundos
- Presiona `Ctrl+C` para detener

### 📋 Ver Estado Rápidamente
```bash
./show_status.sh
# o simplemente:
cat status.txt
```

### 🔄 Generar Estado Manualmente
```bash
python3 status_monitor.py
```

## Monitoreo en Tiempo Real

El sistema incluye un monitor completo que genera un archivo `status.txt` con:

### 📊 Información del Sistema
- Hora actual (Barranquilla UTC-5)
- Uso de CPU y memoria
- Procesos Python activos
- Llamadas programadas

### 💬 Conversaciones Activas
- Estado de cada conversación
- Tiempo desde última interacción
- Llamadas programadas y su estado
- Número de mensajes enviados

### 🎵 Archivos de Audio
- Cantidad y tamaño total
- Archivos más recientes
- Tiempo de creación

### 📝 Archivos de Log
- Historial de conversaciones
- Tamaño y líneas por archivo
- Última modificación

### 🔧 Procesos del Sistema
- Top 5 procesos Python por CPU
- Uso de memoria por proceso

## Estructura de Archivos

```
evaInstance/
├── main.py                 # Servidor principal con lógica de formularios
├── app.py                  # Configuración adicional
├── config_tts.py          # Configuración de TTS
├── requirements.txt       # Dependencias
├── run_server.sh          # Script principal (servidor + monitor)
├── run_monitor.sh         # Script solo monitor
├── show_status.sh         # Script para ver estado
├── status_monitor.py      # Monitor de estado
├── status.txt             # Archivo de estado (generado automáticamente)
├── conversations/         # Estado de conversaciones (generado automáticamente)
├── audio/                # Archivos de audio generados
└── chatlog-*.txt         # Historial de conversaciones por usuario
```

## Monitoreo

- **Estado completo**: `cat status.txt`
- **Estado de conversaciones**: GET `/conversations/status`
- **Logs del servidor**: Revisar salida de consola
- **Archivos de estado**: Directorio `conversations/`
- **Historial de chat**: Archivos `chatlog-*.txt`
