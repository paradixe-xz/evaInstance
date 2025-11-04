# Eva AI Assistant

Un sistema completo de asistente virtual con WhatsApp Business API, llamadas telefónicas e inteligencia artificial.

## Estructura del Proyecto

```
evaInstance/
├── back/           # Backend (FastAPI + Python)
│   ├── app/        # Código principal de la aplicación
│   ├── kani-tts/   # Servicio de Text-to-Speech
│   ├── logs/       # Archivos de log
│   ├── storage/    # Almacenamiento de archivos
│   ├── .env        # Variables de entorno
│   ├── requirements.txt
│   └── start.py    # Script de inicio
├── front/          # Frontend (preparado para React/Vue)
├── .gitignore
└── README.md
```

## Características del Backend

- 🤖 **Integración con IA**: Usa Ollama para conversaciones inteligentes
- 📱 **WhatsApp Business API**: Manejo completo de mensajes de WhatsApp
- 🎤 **Llamadas telefónicas**: Integración con Twilio para llamadas de voz
- 🗣️ **Text-to-Speech**: Síntesis de voz en español usando KaniTTS
- 🎧 **Speech-to-Text**: Reconocimiento de voz para llamadas
- 📊 **Base de datos**: Almacenamiento de conversaciones y usuarios
- 🔄 **API REST**: Endpoints completos para todas las funcionalidades

## 🔄 Flujo de Trabajo

### 1. **Carga de Contactos** 📊
- Subir archivo Excel con columnas `nombre` y `numero`
- Validación automática y limpieza de números
- Programación inmediata de llamadas

### 2. **Llamadas Directas** 📞
- Llamadas automáticas a todos los contactos válidos
- Transcripción completa de toda la conversación
- TTS con KaniTTS para voz natural de alta calidad
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

# KaniTTS
export KANITTS_MODEL=kani-tts-370m
export KANITTS_SPEAKER=es_female_1
export KANITTS_LANGUAGE=es
export KANITTS_DEVICE=auto
export KANITTS_TEMPERATURE=0.7
export KANITTS_TOP_P=0.9

# URL pública para archivos de audio
export PUBLIC_BASE_URL=your_public_url
```

## 🚀 Instalación y Ejecución

### Backend

1. **Navegar al directorio del backend**:
```bash
cd back
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

4. **Iniciar el servidor**:
```bash
python start.py
```

O manualmente:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

El directorio `front/` está preparado para tu aplicación frontend. Se recomienda usar:
- React o Vue.js
- Tailwind CSS para estilos
- Axios para comunicación con la API
- Socket.io para tiempo real

## 🔧 Configuración del Backend

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
- torch
- torchaudio
- transformers
- accelerate
- soundfile
- librosa
- nemo_toolkit
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
- **Configuración optimizada**: KaniTTS configurado para baja latencia y alta calidad

### Beneficios
- **Latencia reducida**: De 9 segundos a menos de 3 segundos
- **Respuestas fluidas**: Audio generado mientras se procesa la IA
- **Mejor UX**: Conversaciones más naturales y rápidas
- **Gestión de memoria**: Limpieza automática de archivos antiguos

## 📞 Soporte

Para soporte técnico o preguntas sobre el sistema, consultar la documentación en `docs/` o contactar al equipo de desarrollo.