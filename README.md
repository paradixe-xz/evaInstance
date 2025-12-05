# 🤖 Eva AI Assistant - Plataforma Completa de Comunicación Inteligente

> Sistema empresarial de comunicación multicanal con IA avanzada, RAG, y gestión inteligente de agentes. Integra WhatsApp, llamadas, emails, SIP trunk, y capacidades de voz con base de conocimiento personalizada.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react)](https://reactjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python)](https://www.python.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Local_AI-000000?style=flat)](https://ollama.ai/)

---

## 📋 Tabla de Contenidos

- [Capacidades Principales](#-capacidades-principales)
- [Características Avanzadas](#-características-avanzadas)
- [Arquitectura](#%EF%B8%8F-arquitectura)
- [Inicio Rápido](#-inicio-rápido)
- [Documentación Completa](#-documentación-completa)
- [API Reference](#-api-reference)
- [Configuración](#-configuración)

---

## 🚀 Capacidades Principales

### 1. 💬 **Mensajería WhatsApp Business**
- ✅ Envío y recepción de mensajes en tiempo real
- ✅ Integración completa con WhatsApp Business API
- ✅ Webhooks para eventos (mensajes, estados, lectura)
- ✅ Gestión de conversaciones multiusuario
- ✅ Respuestas automáticas con IA contextual
- ✅ Análisis de sentimiento y conversaciones
- ✅ Soporte para multimedia (imágenes, audio, documentos)

### 2. 📞 **Sistema de Llamadas Telefónicas**
- ✅ Llamadas entrantes y salientes con Twilio
- ✅ Grabación automática de llamadas
- ✅ Transcripción en tiempo real (STT)
- ✅ Síntesis de voz multiidioma (TTS)
- ✅ IVR (Interactive Voice Response) con IA
- ✅ Logs detallados y analytics
- ✅ Integración con agentes IA para respuestas automáticas

### 3. 📧 **Gestión de Correos Electrónicos**
- ✅ Envío de correos con plantillas
- ✅ Gestión de conversaciones por email
- ✅ Respuestas automáticas inteligentes
- ✅ Integración con chat service
- ✅ Análisis de emails con IA
- ✅ Clasificación automática de mensajes

### 4. 📡 **SIP Trunk Integration**
- ✅ Configuración de múltiples trunks SIP
- ✅ Gestión de credenciales y autenticación
- ✅ Enrutamiento inteligente de llamadas
- ✅ Monitoreo de estado en tiempo real
- ✅ Failover automático
- ✅ Soporte para múltiples proveedores

### 5. 🎙️ **TTS/STT Multi-Engine**
- ✅ **Google Speech Recognition** - STT de alta precisión
- ✅ **KaniTTS** - TTS en español (local, sin internet)
- ✅ **Edge TTS** - TTS de Microsoft con múltiples voces
- ✅ **Coqui TTS** - TTS open source personalizable
- ✅ Procesamiento de audio en tiempo real
- ✅ Soporte para múltiples idiomas
- ✅ Calidad de voz ajustable

### 6. 🤖 **Gestión Avanzada de Agentes IA**
- ✅ Creación de agentes con personalidades personalizadas
- ✅ Integración con Ollama (modelos locales)
- ✅ Chat con streaming en tiempo real
- ✅ Sistema de prompts dinámicos
- ✅ Múltiples agentes simultáneos
- ✅ Activación/desactivación de agentes
- ✅ Testing y validación de agentes
- ✅ Métricas y analytics por agente

---

## 🔥 Características Avanzadas

### 7. 📚 **RAG (Retrieval Augmented Generation)**
- ✅ Base de conocimiento personalizada por agente
- ✅ Búsqueda semántica con embeddings
- ✅ Procesamiento de documentos (PDF, TXT, DOCX, MD)
- ✅ Chunking inteligente de documentos
- ✅ Indexación automática con vectores
- ✅ Respuestas contextualizadas con fuentes
- ✅ Actualización dinámica de conocimiento
- ✅ Estadísticas de uso de knowledge base

**Endpoints RAG:**
```http
POST /api/v1/knowledge/upload          # Subir documentos
GET  /api/v1/knowledge/documents        # Listar documentos
POST /api/v1/knowledge/search           # Búsqueda semántica
DELETE /api/v1/knowledge/{id}           # Eliminar documento
POST /api/v1/knowledge/{id}/reindex     # Reindexar documento
GET  /api/v1/knowledge/stats            # Estadísticas
```

### 8. 📄 **Document Processing**
- ✅ Extracción de texto de PDFs
- ✅ Procesamiento de documentos Word
- ✅ Análisis de Markdown
- ✅ OCR para imágenes (opcional)
- ✅ Chunking inteligente con overlap
- ✅ Metadata extraction
- ✅ Procesamiento asíncrono
- ✅ Progress tracking

### 9. 🧠 **Embeddings Service**
- ✅ Generación de embeddings con Ollama
- ✅ Modelos de embeddings personalizables
- ✅ Caché de embeddings
- ✅ Búsqueda por similitud coseno
- ✅ Batch processing de embeddings
- ✅ Optimización de performance

### 10. 🔄 **Conversation Flows**
- ✅ Flujos de conversación predefinidos
- ✅ Estados de conversación
- ✅ Transiciones automáticas
- ✅ Validación de inputs
- ✅ Contexto persistente
- ✅ Fallback handling
- ✅ Multi-step conversations

**Endpoints Conversation Flows:**
```http
GET  /api/v1/conversation-flows         # Listar flujos
POST /api/v1/conversation-flows         # Crear flujo
GET  /api/v1/conversation-flows/{id}    # Obtener flujo
PUT  /api/v1/conversation-flows/{id}    # Actualizar flujo
DELETE /api/v1/conversation-flows/{id}  # Eliminar flujo
```

### 11. 📊 **Campaign Management**
- ✅ Creación de campañas multicanal
- ✅ Asignación de agentes a campañas
- ✅ Segmentación de audiencias
- ✅ Programación de mensajes
- ✅ Analytics en tiempo real
- ✅ A/B testing
- ✅ ROI tracking

**Endpoints Campaigns:**
```http
GET  /api/v1/campaigns                  # Listar campañas
POST /api/v1/campaigns                  # Crear campaña
GET  /api/v1/campaigns/{id}             # Obtener campaña
PUT  /api/v1/campaigns/{id}             # Actualizar campaña
DELETE /api/v1/campaigns/{id}           # Eliminar campaña
GET  /api/v1/campaigns/{id}/analytics   # Analytics
```

### 12. 🔐 **Authentication & User Management**
- ✅ JWT authentication
- ✅ Role-based access control (RBAC)
- ✅ User registration y login
- ✅ Password hashing con bcrypt
- ✅ Token refresh
- ✅ Session management
- ✅ Multi-user support
- ✅ System users vs regular users

### 13. 📈 **Analytics & Monitoring**
- ✅ Call logs detallados
- ✅ Message tracking
- ✅ Agent performance metrics
- ✅ Conversation analytics
- ✅ Response time tracking
- ✅ Error logging
- ✅ Health checks
- ✅ Real-time dashboards

### 14. 🔌 **Integration Services**
- ✅ Ollama integration para LLMs locales
- ✅ Twilio para llamadas
- ✅ WhatsApp Business API
- ✅ SMTP para emails
- ✅ SIP trunk providers
- ✅ Webhook support
- ✅ REST API completa
- ✅ WebSocket para real-time

---

## 🏗️ Arquitectura

```
evaInstance/
├── client/                          # Frontend React + TypeScript
│   ├── src/
│   │   ├── components/             # Componentes UI
│   │   │   ├── layout/            # Layouts (MainLayout, AuthLayout, AgentLayout)
│   │   │   └── ui/                # UI components (shadcn/ui)
│   │   ├── pages/                 # Páginas
│   │   │   ├── agent/             # Gestión de agentes
│   │   │   ├── whatsapp/          # WhatsApp dashboard
│   │   │   ├── DashboardPage.tsx  # Dashboard principal
│   │   │   ├── LoginPage.tsx      # Autenticación
│   │   │   └── RegisterPage.tsx   # Registro
│   │   ├── services/              # API services
│   │   ├── contexts/              # React contexts (Auth, etc)
│   │   ├── hooks/                 # Custom hooks
│   │   └── config/                # Configuración
│   └── package.json
│
└── server/                          # Backend FastAPI + Python
    ├── app/
    │   ├── api/v1/endpoints/       # REST API Endpoints
    │   │   ├── whatsapp.py        # 💬 WhatsApp messaging
    │   │   ├── calls.py           # 📞 Llamadas y voz
    │   │   ├── email.py           # 📧 Correos
    │   │   ├── sip.py             # 📡 SIP trunk
    │   │   ├── chat.py            # 💬 Chat con agentes
    │   │   └── conversation_flows.py # 🔄 Flujos de conversación
    │   │
    │   ├── services/               # Business Logic
    │   │   ├── agent_service.py   # 🤖 Gestión de agentes
    │   │   ├── ollama_service.py  # 🧠 Integración Ollama
    │   │   ├── rag_service.py     # 📚 RAG implementation
    │   │   ├── knowledge_service.py # 📄 Knowledge base
    │   │   ├── embedding_service.py # 🧠 Embeddings
    │   │   ├── document_processor.py # 📄 Procesamiento docs
    │   │   ├── chat_service.py    # 💬 Chat management
    │   │   ├── conversation_service.py # 🔄 Conversation flows
    │   │   ├── whatsapp_service.py # 💬 WhatsApp
    │   │   ├── call_service.py    # 📞 Llamadas
    │   │   ├── email_service.py   # 📧 Email
    │   │   ├── email_chat_service.py # 📧 Email + Chat
    │   │   ├── sip_service.py     # 📡 SIP
    │   │   ├── stt_service.py     # 🎙️ Speech-to-Text
    │   │   ├── kanitts_service.py # 🔊 KaniTTS
    │   │   ├── edge_tts_service.py # 🔊 Edge TTS
    │   │   ├── coqui_service.py   # 🔊 Coqui TTS
    │   │   └── auth_service.py    # 🔐 Authentication
    │   │
    │   ├── models/                 # Database Models (SQLAlchemy)
    │   │   ├── user.py            # Usuarios
    │   │   ├── system_user.py     # Usuarios del sistema
    │   │   ├── agent.py           # Agentes IA
    │   │   ├── chat.py            # Sesiones de chat
    │   │   ├── campaign.py        # Campañas
    │   │   ├── call_log.py        # Logs de llamadas
    │   │   ├── sip_trunk.py       # SIP trunks
    │   │   ├── knowledge_document.py # Documentos
    │   │   └── knowledge_chunk.py # Chunks de documentos
    │   │
    │   ├── repositories/           # Data Access Layer
    │   ├── schemas/                # Pydantic Schemas
    │   └── core/                   # Core utilities
    │       ├── config.py          # Configuración
    │       ├── database.py        # Database setup
    │       ├── logging.py         # Logging config
    │       └── exceptions.py      # Custom exceptions
    │
    ├── kani-tts/                   # Servicio TTS local
    ├── storage/                    # Almacenamiento de archivos
    │   └── knowledge/             # Documentos de knowledge base
    ├── logs/                       # Application logs
    ├── migrations/                 # Database migrations
    ├── requirements.txt            # Python dependencies
    ├── start.py                    # Startup script
    └── whatsapp_ai.db             # SQLite database
```

---

## ⚡ Inicio Rápido

### Prerrequisitos
- **Python 3.11+**
- **Node.js 18+**
- **Ollama** instalado y ejecutándose ([Descargar](https://ollama.ai/))
- (Opcional) Cuenta de Twilio para llamadas
- (Opcional) WhatsApp Business API access
- (Opcional) Cuenta SMTP para emails

### 1. Clonar el Repositorio
```bash
git clone <repository-url>
cd evaInstance
```

### 2. Configurar el Backend
```bash
cd server

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\\Scripts\\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Inicializar base de datos
python init_db.py

# Iniciar servidor
python start.py
```

Backend disponible en: `http://localhost:8000`

### 3. Configurar el Frontend
```bash
cd client

# Instalar dependencias
npm install

# Configurar API URL
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env

# Iniciar desarrollo
npm run dev
```

Frontend disponible en: `http://localhost:5173`

### 4. Configurar Ollama
```bash
# Instalar un modelo base
ollama pull llama2

# Verificar instalación
ollama list
```

### 5. Acceder a la Aplicación
1. Abrir `http://localhost:5173`
2. Registrarse con un nuevo usuario
3. Crear tu primer agente IA
4. ¡Empezar a chatear!

---

## 📚 Documentación Completa

### 🤖 Gestión de Agentes IA

#### Crear Agente con Ollama
```python
POST /api/v1/agents/ollama/create
{
  "name": "Asistente de Ventas",
  "base_model": "llama2",
  "system_prompt": "Eres un experto asistente de ventas...",
  "temperature": 0.7,
  "max_tokens": 2000,
  "description": "Agente especializado en ventas"
}
```

#### Chat con Streaming
```python
POST /api/v1/agents/ollama/{agent_id}/chat/stream
{
  "message": "¿Cuáles son nuestros productos?",
  "session_id": "session-123",
  "use_knowledge_base": true  # Usar RAG
}

# Respuesta en streaming (Server-Sent Events)
```

#### Gestión de Agentes
```python
GET    /api/v1/agents                    # Listar todos
GET    /api/v1/agents/{id}               # Obtener uno
PUT    /api/v1/agents/{id}               # Actualizar
DELETE /api/v1/agents/{id}               # Eliminar
POST   /api/v1/agents/{id}/activate      # Activar
POST   /api/v1/agents/{id}/deactivate    # Desactivar
POST   /api/v1/agents/{id}/test          # Probar agente
```

---

### 📚 RAG & Knowledge Base

#### Subir Documento
```python
POST /api/v1/knowledge/upload
Content-Type: multipart/form-data

agent_id: 123
file: documento.pdf
title: "Manual de Productos"
description: "Catálogo completo de productos 2024"

# Respuesta
{
  "document_id": 456,
  "status": "processing",
  "chunks_created": 0,
  "message": "Document uploaded, processing started"
}
```

#### Búsqueda Semántica
```python
POST /api/v1/knowledge/search
{
  "agent_id": 123,
  "query": "¿Cuál es el precio del producto X?",
  "limit": 5,
  "threshold": 0.7
}

# Respuesta
{
  "results": [
    {
      "chunk_id": 789,
      "content": "El producto X tiene un precio de $99.99...",
      "similarity": 0.89,
      "document_title": "Manual de Productos",
      "page": 15
    }
  ]
}
```

#### Estadísticas de Knowledge Base
```python
GET /api/v1/knowledge/stats?agent_id=123

# Respuesta
{
  "total_documents": 25,
  "total_chunks": 1250,
  "total_size_bytes": 15728640,
  "processed_documents": 23,
  "pending_documents": 2,
  "avg_chunks_per_document": 50
}
```

---

### 💬 WhatsApp Business

#### Enviar Mensaje
```python
POST /api/v1/whatsapp/send-message
{
  "to": "+1234567890",
  "message": "Hola, ¿cómo puedo ayudarte hoy?"
}
```

#### Webhook (Recibir Mensajes)
```python
POST /api/v1/whatsapp/webhook
# WhatsApp enviará automáticamente los mensajes aquí
# El sistema procesará y responderá automáticamente con IA
```

#### Obtener Conversaciones
```python
GET /api/v1/whatsapp/conversations?limit=50&offset=0

# Respuesta
{
  "conversations": [
    {
      "phone_number": "+1234567890",
      "last_message": "Gracias por tu ayuda",
      "last_message_time": "2024-12-04T20:30:00",
      "unread_count": 2,
      "agent_id": 123
    }
  ]
}
```

---

### 📞 Sistema de Llamadas

#### Llamada Entrante (Twilio Webhook)
```python
POST /api/v1/calls/incoming
# Twilio enviará automáticamente las llamadas aquí
# El sistema responderá con TTS y procesará con STT
```

#### Transcribir Audio
```python
POST /api/v1/calls/stt/transcribe
Content-Type: multipart/form-data

file: audio.wav
language: es-ES

# Respuesta
{
  "transcription": "Hola, necesito información sobre sus productos",
  "confidence": 0.95,
  "language": "es-ES"
}
```

#### Generar Audio TTS
```python
POST /api/v1/calls/tts/generate
{
  "text": "Bienvenido a Eva AI Assistant",
  "language": "es",
  "engine": "kanitts"  # kanitts, edge, coqui
}

# Respuesta: archivo de audio WAV
```

#### Logs de Llamadas
```python
GET /api/v1/calls/logs?limit=100&offset=0

# Respuesta
{
  "logs": [
    {
      "call_id": "CA123",
      "from_number": "+1234567890",
      "to_number": "+0987654321",
      "duration": 180,
      "status": "completed",
      "recording_url": "https://...",
      "transcription": "...",
      "timestamp": "2024-12-04T20:00:00"
    }
  ]
}
```

---

### 📧 Gestión de Emails

#### Enviar Email
```python
POST /api/v1/email/send
{
  "to": "cliente@example.com",
  "subject": "Bienvenido a Eva AI",
  "body": "Gracias por contactarnos...",
  "html": true
}
```

#### Chat por Email (con IA)
```python
POST /api/v1/email/chat
{
  "email": "cliente@example.com",
  "message": "Necesito información sobre precios",
  "agent_id": 123
}

# El sistema enviará un email con la respuesta del agente IA
```

---

### 📡 SIP Trunk

#### Crear SIP Trunk
```python
POST /api/v1/sip/trunks
{
  "name": "Mi Trunk Principal",
  "host": "sip.provider.com",
  "port": 5060,
  "username": "myuser",
  "password": "mypass",
  "protocol": "UDP",
  "enabled": true
}
```

#### Verificar Estado
```python
GET /api/v1/sip/trunks/{id}/status

# Respuesta
{
  "trunk_id": 123,
  "status": "online",
  "last_check": "2024-12-04T20:00:00",
  "active_calls": 5,
  "total_calls_today": 150
}
```

---

### 🔄 Conversation Flows

#### Crear Flujo
```python
POST /api/v1/conversation-flows
{
  "name": "Flujo de Ventas",
  "description": "Flujo para calificar leads",
  "steps": [
    {
      "id": "welcome",
      "message": "¡Hola! ¿En qué puedo ayudarte?",
      "next_step": "ask_product"
    },
    {
      "id": "ask_product",
      "message": "¿Qué producto te interesa?",
      "validation": "required",
      "next_step": "ask_budget"
    }
  ]
}
```

---

## 🔧 Configuración

### Variables de Entorno Completas

```bash
# ============================================
# APLICACIÓN
# ============================================
APP_NAME="Eva AI Assistant"
DEBUG=true
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# ============================================
# BASE DE DATOS
# ============================================
DATABASE_URL=sqlite:///./whatsapp_ai.db

# ============================================
# OLLAMA (IA)
# ============================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_TEMPERATURE=0.7
OLLAMA_MAX_TOKENS=2000
OLLAMA_TIMEOUT=120

# ============================================
# WHATSAPP BUSINESS API
# ============================================
WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_verify_token
WHATSAPP_API_VERSION=v18.0

# ============================================
# TWILIO (LLAMADAS)
# ============================================
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_RECORDING_ENABLED=true

# ============================================
# EMAIL (SMTP)
# ============================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_NAME=Eva AI Assistant
SMTP_USE_TLS=true

# ============================================
# SIP TRUNK
# ============================================
SIP_TRUNK_HOST=sip.provider.com
SIP_TRUNK_PORT=5060
SIP_TRUNK_USERNAME=your_username
SIP_TRUNK_PASSWORD=your_password
SIP_TRUNK_PROTOCOL=UDP

# ============================================
# TTS/STT
# ============================================
# Google Speech Recognition
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# KaniTTS
KANITTS_HOST=localhost
KANITTS_PORT=5002

# Edge TTS
EDGE_TTS_VOICE=es-ES-ElviraNeural

# Coqui TTS
COQUI_TTS_MODEL=tts_models/es/css10/vits

# ============================================
# JWT AUTHENTICATION
# ============================================
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ============================================
# STORAGE
# ============================================
STORAGE_PATH=./storage
KNOWLEDGE_BASE_PATH=./storage/knowledge
MAX_UPLOAD_SIZE_MB=50

# ============================================
# RAG CONFIGURATION
# ============================================
CHUNK_SIZE=500
CHUNK_OVERLAP=50
SIMILARITY_THRESHOLD=0.7
MAX_SEARCH_RESULTS=5

# ============================================
# LOGGING
# ============================================
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5
```

---

## 🛠️ Stack Tecnológico

### Backend
- **FastAPI** - Framework web moderno y rápido
- **SQLAlchemy** - ORM para base de datos
- **Pydantic** - Validación de datos
- **Ollama** - Modelos de lenguaje locales
- **LangChain** - Framework para aplicaciones LLM
- **Twilio** - Llamadas telefónicas
- **WhatsApp Business API** - Mensajería
- **Google Speech Recognition** - STT
- **KaniTTS / Edge TTS / Coqui TTS** - TTS
- **JWT** - Autenticación
- **Bcrypt** - Hashing de contraseñas

### Frontend
- **React 19** - Framework UI
- **TypeScript** - Tipado estático
- **Vite** - Build tool ultrarrápido
- **Tailwind CSS** - Framework CSS utility-first
- **shadcn/ui** - Componentes UI
- **React Query** - Gestión de estado del servidor
- **Zod** - Validación de esquemas
- **React Hook Form** - Gestión de formularios
- **Sonner** - Toast notifications

### Base de Datos
- **SQLite** - Base de datos local (desarrollo)
- **PostgreSQL** - Base de datos (producción recomendada)

**Tablas:**
- `users` - Usuarios de WhatsApp
- `system_users` - Usuarios del sistema
- `agents` - Agentes IA
- `chat_sessions` - Sesiones de chat
- `messages` - Mensajes
- `call_logs` - Logs de llamadas
- `sip_trunks` - Configuraciones SIP
- `campaigns` - Campañas
- `knowledge_documents` - Documentos de knowledge base
- `knowledge_chunks` - Chunks de documentos con embeddings

---

## 📊 API Reference Completa

### 🔐 Autenticación
```http
POST   /api/v1/auth/signup           # Registro
POST   /api/v1/auth/login            # Login
POST   /api/v1/auth/refresh          # Refresh token
GET    /api/v1/auth/me               # Usuario actual
```

### 🤖 Agentes
```http
GET    /api/v1/agents                # Listar agentes
POST   /api/v1/agents/ollama/create  # Crear agente Ollama
GET    /api/v1/agents/{id}           # Obtener agente
PUT    /api/v1/agents/{id}           # Actualizar agente
DELETE /api/v1/agents/{id}           # Eliminar agente
POST   /api/v1/agents/{id}/activate  # Activar
POST   /api/v1/agents/{id}/deactivate # Desactivar
POST   /api/v1/agents/{id}/test      # Probar agente
GET    /api/v1/agents/base-models    # Modelos disponibles
```

### 💬 Chat
```http
POST   /api/v1/agents/ollama/{id}/chat/stream  # Chat streaming
GET    /api/v1/chat/sessions                   # Sesiones
POST   /api/v1/chat/sessions                   # Nueva sesión
GET    /api/v1/chat/sessions/{id}/messages     # Mensajes
```

### 📚 Knowledge Base (RAG)
```http
POST   /api/v1/knowledge/upload       # Subir documento
GET    /api/v1/knowledge/documents     # Listar documentos
GET    /api/v1/knowledge/documents/{id} # Obtener documento
DELETE /api/v1/knowledge/documents/{id} # Eliminar documento
POST   /api/v1/knowledge/search        # Búsqueda semántica
GET    /api/v1/knowledge/stats         # Estadísticas
POST   /api/v1/knowledge/{id}/reindex  # Reindexar
```

### 💬 WhatsApp
```http
POST   /api/v1/whatsapp/webhook        # Webhook
POST   /api/v1/whatsapp/send-message   # Enviar mensaje
GET    /api/v1/whatsapp/conversations  # Conversaciones
```

### 📞 Llamadas
```http
POST   /api/v1/calls/incoming          # Llamada entrante
POST   /api/v1/calls/outgoing          # Llamada saliente
POST   /api/v1/calls/stt/transcribe    # Transcribir audio
POST   /api/v1/calls/tts/generate      # Generar TTS
GET    /api/v1/calls/logs              # Logs de llamadas
GET    /api/v1/calls/kanitts/status    # Estado KaniTTS
```

### 📧 Email
```http
POST   /api/v1/email/send              # Enviar email
GET    /api/v1/email/conversations     # Conversaciones
POST   /api/v1/email/chat              # Chat por email
```

### 📡 SIP Trunk
```http
GET    /api/v1/sip/trunks              # Listar trunks
POST   /api/v1/sip/trunks              # Crear trunk
GET    /api/v1/sip/trunks/{id}         # Obtener trunk
PUT    /api/v1/sip/trunks/{id}         # Actualizar trunk
DELETE /api/v1/sip/trunks/{id}         # Eliminar trunk
GET    /api/v1/sip/trunks/{id}/status  # Estado trunk
```

### 🔄 Conversation Flows
```http
GET    /api/v1/conversation-flows      # Listar flujos
POST   /api/v1/conversation-flows      # Crear flujo
GET    /api/v1/conversation-flows/{id} # Obtener flujo
PUT    /api/v1/conversation-flows/{id} # Actualizar flujo
DELETE /api/v1/conversation-flows/{id} # Eliminar flujo
```

### 📊 Campaigns
```http
GET    /api/v1/campaigns               # Listar campañas
POST   /api/v1/campaigns               # Crear campaña
GET    /api/v1/campaigns/{id}          # Obtener campaña
PUT    /api/v1/campaigns/{id}          # Actualizar campaña
DELETE /api/v1/campaigns/{id}          # Eliminar campaña
GET    /api/v1/campaigns/{id}/analytics # Analytics
```

---

## 🚦 Health Checks & Monitoring

```bash
# Backend health
curl http://localhost:8000/health

# API docs
curl http://localhost:8000/docs

# KaniTTS status
curl http://localhost:8000/api/v1/calls/kanitts/status

# Ollama status
curl http://localhost:11434/api/tags

# Database check
curl http://localhost:8000/api/v1/health/db
```

---

## 📈 Características de Producción

- ✅ **Logging estructurado** con niveles configurables
- ✅ **Error handling** robusto con custom exceptions
- ✅ **Rate limiting** para APIs
- ✅ **CORS** configurado
- ✅ **Database migrations** con Alembic
- ✅ **Async processing** para tareas pesadas
- ✅ **Caching** de embeddings y respuestas
- ✅ **Health checks** para todos los servicios
- ✅ **Monitoring** con métricas
- ✅ **Backup** automático de base de datos
- ✅ **Security** con JWT y bcrypt
- ✅ **API versioning** (v1)
- ✅ **Documentation** automática con OpenAPI

---

## 🔒 Seguridad

- 🔐 JWT authentication con refresh tokens
- 🔐 Password hashing con bcrypt
- 🔐 CORS configurado
- 🔐 Rate limiting
- 🔐 Input validation con Pydantic
- 🔐 SQL injection protection con SQLAlchemy
- 🔐 Environment variables para secretos
- 🔐 HTTPS recomendado en producción

---

## 📝 Licencia

Uso interno - Épico Marketing Digital

---

## 🤝 Soporte

Para soporte técnico y consultas, contacta al equipo de desarrollo.

---

**Última Actualización**: Diciembre 2025  
**Versión**: 3.0.0  
**Estado**: ✅ Producción - Sistema Completo y Robusto