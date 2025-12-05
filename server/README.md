# Eva AI Assistant - Server

Backend unificado del sistema Eva AI Assistant con FastAPI, WhatsApp Business API, y servicios de IA.

## 🏗️ Estructura del Servidor

```
server/
├── app/                    # Aplicación principal FastAPI
│   ├── api/               # Endpoints de la API
│   ├── core/              # Configuración y utilidades
│   ├── models/            # Modelos de datos (SQLAlchemy)
│   ├── services/          # Servicios de negocio
│   ├── repositories/      # Capa de acceso a datos
│   ├── schemas/           # Validación de datos (Pydantic)
│   └── middleware/        # Middleware personalizado
├── modules/               # Módulos adicionales opcionales
│   ├── dermaccina/        # Backend Node.js/TypeScript
│   └── sync-elevenlabs/   # Servicio de sincronización ElevenLabs
├── kani-tts/             # Servicio de Text-to-Speech
├── storage/              # Almacenamiento de archivos
├── logs/                 # Logs del sistema
├── migrations/           # Migraciones de base de datos
├── requirements.txt      # Dependencias Python
├── start.py             # Script de inicio
├── .env                 # Variables de entorno
└── whatsapp_ai.db       # Base de datos SQLite
```

## 🚀 Inicio Rápido

### Servidor Principal (FastAPI)

```bash
# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor
python start.py

# O manualmente con uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

El servidor estará disponible en `http://localhost:8000`

### Módulos Adicionales (Opcionales)

#### Dermaccina (Node.js)
```bash
cd modules/dermaccina
npm install
npm run dev
```

#### Sync ElevenLabs
```bash
cd modules/sync-elevenlabs
npm install
npm start
```

## 🔧 Configuración

### Variables de Entorno

Copia `.env.example` a `.env` y configura las siguientes variables:

```bash
# Aplicación
APP_NAME="WhatsApp AI Backend"
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Base de datos
DATABASE_URL=sqlite:///./whatsapp_ai.db

# Ollama (IA)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=ema
OLLAMA_TEMPERATURE=0.7

# WhatsApp (opcional)
WHATSAPP_ACCESS_TOKEN=your_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_id

# Twilio (opcional)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=your_number
```

## 📚 API Documentation

Una vez iniciado el servidor, la documentación interactiva está disponible en:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 Endpoints Principales

### Autenticación
- `POST /api/v1/auth/login` - Iniciar sesión
- `POST /api/v1/auth/signup` - Registro de usuarios

### Agentes
- `GET /api/v1/agents` - Listar agentes
- `POST /api/v1/agents/ollama/create` - Crear agente
- `POST /api/v1/agents/ollama/{id}/chat/stream` - Chat con streaming

### Llamadas y Voz
- `POST /api/v1/calls/stt/transcribe` - Transcribir audio
- `POST /api/v1/calls/tts/generate` - Generar audio TTS
- `GET /api/v1/calls/kanitts/status` - Estado de KaniTTS

## 🛠️ Stack Tecnológico

- **FastAPI** - Framework web moderno
- **SQLAlchemy** - ORM de base de datos
- **Pydantic** - Validación de datos
- **Ollama** - Modelos de lenguaje local
- **KaniTTS** - Text-to-Speech en español
- **Twilio** - Llamadas telefónicas
- **WhatsApp Business API** - Mensajería

## 📦 Módulos Adicionales

### Dermaccina
Backend Node.js/TypeScript con Express y Sequelize para funcionalidad específica de dermaccina.

### Sync ElevenLabs
Servicio de sincronización de conversaciones de ElevenLabs a PostgreSQL.

## 🔍 Troubleshooting

### El servidor no inicia
- Verificar que el puerto 8000 esté libre
- Revisar que todas las dependencias estén instaladas
- Verificar que el archivo `.env` exista

### Ollama no responde
- Verificar que Ollama esté ejecutándose: `curl http://localhost:11434/api/tags`
- Revisar que el modelo esté instalado

### KaniTTS no funciona
- Verificar estado: `GET /api/v1/calls/kanitts/status`
- Revisar logs en `logs/`

## 📝 Logs

Los logs del sistema se almacenan en la carpeta `logs/`:
- `app.log` - Logs generales de la aplicación
- `error.log` - Logs de errores

## 🗄️ Base de Datos

El servidor usa SQLite por defecto (`whatsapp_ai.db`). Para inicializar o migrar la base de datos:

```bash
# Inicializar base de datos
python init_db.py

# Ejecutar migraciones
python run_migration.py
```

## 📄 Licencia

Uso interno - Épico Marketing Digital
