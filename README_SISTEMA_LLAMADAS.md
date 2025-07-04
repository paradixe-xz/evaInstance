# Sistema ANA - Llamadas Directas con Análisis de IA

## 🎯 Descripción General

El sistema ANA ha sido completamente renovado para implementar un flujo de **llamadas directas automáticas** con **transcripción completa** y **análisis inteligente de IA** para determinar el seguimiento humano necesario.

## 🔄 Nuevo Flujo de Trabajo

### 1. **Carga de Contactos** 📊
- Subir archivo Excel con columnas `nombre` y `numero`
- El sistema valida y limpia los números automáticamente
- **NO hay mensajes de WhatsApp iniciales**

### 2. **Llamadas Directas** 📞
- **Llamadas inmediatas** a todos los contactos válidos
- Transcripción completa de toda la conversación
- Guión de 10 minutos optimizado para ventas
- TTS con ElevenLabs para voz natural

### 3. **Análisis Automático de IA** 🤖
- Análisis completo de la transcripción
- Determinación del nivel de interés
- Identificación de objeciones y puntos clave
- Asignación de prioridad para seguimiento

### 4. **Seguimiento Humano** 👥
- Conversaciones listas para cierre humano
- Información completa de análisis disponible
- Sistema de marcado de resultados

## 📁 Estructura de Archivos

```
evaInstance/
├── main.py                          # Servidor principal
├── conversations/                   # Estados de conversaciones
│   └── conversation-{numero}.json
├── transcripts/                     # Transcripciones completas
│   └── transcript-{numero}.json
├── analysis/                        # Análisis de IA
│   └── analysis-{numero}.json
├── audio/                          # Archivos de audio TTS
└── test_call_system.py             # Script de pruebas
```

## 🔧 Endpoints Principales

### POST `/sendNumbers`
**Procesa archivo Excel y programa llamadas directas**

```bash
curl -X POST "http://localhost:8000/sendNumbers" \
  -F "file=@contactos.xlsx"
```

**Respuesta:**
```json
{
  "message": "Procesamiento completado. 5 llamadas programadas.",
  "total_contacts": 5,
  "valid_contacts": 5,
  "invalid_contacts": 0,
  "results": [
    {
      "numero": "+573001234567",
      "nombre": "Juan Pérez",
      "status": "llamada_programada",
      "call_sid": "CA1234567890"
    }
  ]
}
```

### GET `/conversations/status`
**Estado de todas las conversaciones**

```bash
curl "http://localhost:8000/conversations/status"
```

**Respuesta:**
```json
{
  "total_conversations": 3,
  "current_time": "2024-01-15T14:30:00-05:00",
  "conversations": [
    {
      "number": "+573001234567",
      "name": "Juan Pérez",
      "stage": "call_completed",
      "call_duration": 420,
      "transcript_ready": true,
      "analysis_ready": true,
      "ai_analysis": {
        "interest_level": "high",
        "priority": "high"
      }
    }
  ]
}
```

### GET `/analysis/ready_for_human`
**Conversaciones listas para seguimiento humano**

```bash
curl "http://localhost:8000/analysis/ready_for_human"
```

**Respuesta:**
```json
{
  "total_ready": 2,
  "conversations": [
    {
      "number": "+573001234567",
      "name": "Juan Pérez",
      "call_duration": 420,
      "ai_analysis": {
        "interest_level": "high",
        "objections": ["precio"],
        "key_points": ["necesita $50M"],
        "next_action": "schedule_meeting",
        "human_followup_needed": true,
        "priority": "high",
        "summary": "Cliente muy interesado, necesita $50M",
        "recommendations": ["Llamar inmediatamente", "Ofrecer reunión"]
      },
      "transcript": {
        "conversation": [
          {
            "role": "assistant",
            "content": "¡Alóoo Juan! ¿Cómo estás mi cielo?",
            "timestamp": "2024-01-15T14:25:00-05:00"
          },
          {
            "role": "user", 
            "content": "Hola, estoy bien. ¿En qué puedo ayudarte?",
            "timestamp": "2024-01-15T14:25:05-05:00"
          }
        ]
      }
    }
  ]
}
```

### POST `/analysis/mark_closed`
**Marca conversación como cerrada por humano**

```bash
curl -X POST "http://localhost:8000/analysis/mark_closed" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "+573001234567",
    "outcome": "interested",
    "notes": "Cliente muy interesado, agendó reunión"
  }'
```

## 📊 Estados de Conversación

| Estado | Descripción |
|--------|-------------|
| `initial` | Contacto cargado, esperando llamada |
| `call_in_progress` | Llamada en curso |
| `call_completed` | Llamada terminada, pendiente análisis |
| `analyzed` | Análisis de IA completado |
| `ready_for_human` | Listo para seguimiento humano |
| `closed_by_human` | Cerrado por persona real |

## 🤖 Análisis de IA

El sistema analiza automáticamente cada transcripción y determina:

### Nivel de Interés
- **high**: Muy interesado, necesita seguimiento inmediato
- **medium**: Interesado moderado, seguimiento normal
- **low**: Poco interés, seguimiento básico
- **none**: Sin interés, no requiere seguimiento

### Acciones Recomendadas
- `schedule_meeting`: Agendar reunión
- `send_info`: Enviar información
- `follow_up_call`: Llamada de seguimiento
- `close_deal`: Cerrar trato
- `no_interest`: Sin interés

### Prioridades
- **high**: Seguimiento inmediato (máximo 1 hora)
- **normal**: Seguimiento en 24 horas
- **low**: Seguimiento en 48-72 horas

## 🎤 Transcripción Completa

Cada llamada se transcribe completamente con:

```json
{
  "call_sid": "CA1234567890",
  "number": "+573001234567",
  "name": "Juan Pérez",
  "start_time": "2024-01-15T14:25:00-05:00",
  "end_time": "2024-01-15T14:32:00-05:00",
  "call_duration": 420,
  "conversation": [
    {
      "role": "assistant",
      "content": "¡Alóoo Juan! ¿Cómo estás mi cielo?",
      "timestamp": "2024-01-15T14:25:00-05:00"
    },
    {
      "role": "user",
      "content": "Hola, estoy bien. ¿En qué puedo ayudarte?",
      "timestamp": "2024-01-15T14:25:05-05:00"
    }
  ]
}
```

## 🧪 Pruebas del Sistema

Ejecuta el script de pruebas para verificar que todo funciona:

```bash
python test_call_system.py
```

Este script prueba:
- ✅ Conexión al servidor
- ✅ Sistema TTS
- ✅ Subida de contactos
- ✅ Estado de conversaciones
- ✅ Análisis listo para humano
- ✅ Marcado como cerrado

## 🚀 Configuración

### Variables de Entorno Requeridas

```bash
# Twilio
export TWILIO_ACCOUNT_SID=your_account_sid
export TWILIO_AUTH_TOKEN=your_auth_token
export TWILIO_PHONE_NUMBER=your_phone_number
export TWILIO_WEBHOOK_URL=your_webhook_url

# ElevenLabs
export ELEVENLABS_API_KEY=your_api_key
export ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# URL pública para archivos de audio
export PUBLIC_BASE_URL=your_public_url
```

### Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python main.py

# En otra terminal, ejecutar pruebas
python test_call_system.py
```

## 📋 Formato del Archivo Excel

El archivo debe contener:

| nombre | numero |
|--------|--------|
| Juan Pérez | +573001234567 |
| María García | 3001234568 |
| Carlos López | +573001234569 |

**Notas:**
- La columna `numero` es obligatoria
- La columna `nombre` es opcional pero recomendada
- Los números se limpian automáticamente
- Mínimo 10 dígitos por número

## 🎯 Ventajas del Nuevo Sistema

1. **Eficiencia**: Llamadas directas sin intermediarios
2. **Transparencia**: Transcripción completa de cada conversación
3. **Inteligencia**: Análisis automático con IA
4. **Priorización**: Sistema inteligente de prioridades
5. **Seguimiento**: Información completa para humanos
6. **Escalabilidad**: Manejo automático de múltiples contactos

## 🔄 Flujo Completo de Trabajo

```
1. Cargar Excel → 2. Llamadas automáticas → 3. Transcripción → 4. Análisis IA → 5. Seguimiento humano
```

## 📞 Webhooks de Twilio

El sistema maneja automáticamente:

- **POST `/twilio/voice`**: Inicio de llamada
- **POST `/twilio/voice/handle_speech`**: Reconocimiento de voz
- **POST `/twilio/voice/call_ended`**: Finalización y análisis

## 🎉 Resultado Final

El sistema ahora:
- ✅ Llama directamente a todos los contactos
- ✅ Transcribe completamente cada conversación
- ✅ Analiza automáticamente con IA
- ✅ Asigna prioridades inteligentes
- ✅ Prepara información para cierre humano
- ✅ Permite seguimiento estructurado

¡El sistema está listo para maximizar las conversiones con mínima intervención humana! 