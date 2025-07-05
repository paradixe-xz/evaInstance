# Sistema ANA - Asistente de IA para Préstamos por Libranza

## 🎯 Descripción General

Sistema de IA conversacional especializado en asesoría financiera para préstamos por libranza, con capacidad de llamadas directas, transcripción completa y análisis inteligente para determinar el seguimiento humano necesario.

## 🔄 Flujo de Trabajo

### 1. **Carga de Contactos** 📊
- Subir archivo Excel con columnas `nombre` y `numero`
- Validación automática y limpieza de números
- Programación inmediata de llamadas

### 2. **Llamadas Directas** 📞
- Llamadas automáticas a todos los contactos válidos
- Transcripción completa de toda la conversación
- TTS con ElevenLabs para voz natural
- Guión optimizado para ventas de préstamos

### 3. **Análisis Automático de IA** 🤖
- Análisis completo de la transcripción
- Determinación del nivel de interés
- Identificación de objeciones y puntos clave
- Asignación de prioridad para seguimiento

### 4. **Seguimiento Humano** 👥
- Conversaciones listas para cierre humano
- Información completa de análisis disponible
- Sistema de marcado de resultados

## 📁 Estructura del Proyecto

```
evaInstance/
├── src/
│   ├── api/           # API endpoints (mainApi.py)
│   ├── core/          # Lógica principal (mainApp.py, statusMonitor.py)
│   ├── config/        # Configuraciones (configTts.py)
│   └── utils/         # Utilidades
├── scripts/           # Scripts de ejecución y mantenimiento
├── docs/              # Documentación
├── tests/             # Archivos de prueba
├── data/              # Datos del sistema
│   ├── conversations/ # Estados de conversaciones
│   ├── transcripts/   # Transcripciones completas
│   ├── analysis/      # Análisis de IA
│   └── audio/         # Archivos de audio TTS
└── requirements.txt   # Dependencias
```

## 🔧 Configuración

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

## 🚀 Instalación y Ejecución

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno
```bash
# Copiar y configurar las variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### 3. Ejecutar el servidor
```bash
# Opción 1: Directo
python src/api/mainApi.py

# Opción 2: Con script
chmod +x scripts/runServer.sh
./scripts/runServer.sh
```

## 📊 Endpoints Principales

### POST `/sendNumbers`
Procesa archivo Excel y programa llamadas directas

```bash
curl -X POST "http://localhost:8000/sendNumbers" \
  -F "file=@contactos.xlsx"
```

### GET `/conversations/status`
Estado de todas las conversaciones

```bash
curl "http://localhost:8000/conversations/status"
```

### GET `/analysis/ready_for_human`
Conversaciones listas para seguimiento humano

```bash
curl "http://localhost:8000/analysis/ready_for_human"
```

### POST `/analysis/mark_closed`
Marca conversación como cerrada

```bash
curl -X POST "http://localhost:8000/analysis/mark_closed" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "+573001234567",
    "outcome": "interested",
    "notes": "Cliente muy interesado, agendó reunión"
  }'
```

## 📈 Estados de Conversación

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

## 🛠️ Scripts de Mantenimiento

### Ejecutar servidor
```bash
./scripts/runServer.sh
```

### Reiniciar sistema
```bash
./scripts/restartServer.sh
```

### Actualizar modelo ANA
```bash
./scripts/updateAnaModel.sh
```

### Monitorear estado
```bash
./scripts/showStatus.sh
```

## 📋 Dependencias

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

## 🔍 Monitoreo

El sistema incluye herramientas de monitoreo:

- **Estado de conversaciones**: `/conversations/status`
- **Análisis listos**: `/analysis/ready_for_human`
- **Estadísticas de audio**: `/audio-stats`
- **Limpieza de audio**: `/cleanup-audio`
- **Logs de transcripciones**: En `data/transcripts/`
- **Análisis de IA**: En `data/analysis/`

## ⚡ Optimizaciones de Rendimiento

### Streaming de Audio
- **Streaming de IA**: Procesamiento en chunks para reducir latencia
- **Procesamiento paralelo**: Generación de audio en threads separados
- **Colas de audio**: Gestión eficiente por número de teléfono
- **Configuración optimizada**: ElevenLabs configurado para velocidad

### Beneficios
- **Latencia reducida**: De 9 segundos a menos de 3 segundos
- **Respuestas fluidas**: Audio generado mientras se procesa la IA
- **Mejor UX**: Conversaciones más naturales y rápidas
- **Gestión de memoria**: Limpieza automática de archivos antiguos

## 📞 Soporte

Para soporte técnico o preguntas sobre el sistema, consultar la documentación en `docs/` o contactar al equipo de desarrollo. 