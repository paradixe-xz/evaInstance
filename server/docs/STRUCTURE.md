# Eva AI Assistant - Server Structure

## 📁 Directory Organization

```
server/
├── app/                        # Main application code
│   ├── api/                   # API layer
│   │   └── v1/               # API version 1
│   │       ├── endpoints/    # API endpoints
│   │       ├── analytics.py  # Analytics endpoints
│   │       ├── health.py     # Health check endpoints
│   │       └── webhooks.py   # Webhooks management
│   │
│   ├── core/                  # Core functionality
│   │   ├── cache.py          # Caching layer
│   │   ├── config.py         # Configuration
│   │   ├── database.py       # Database setup
│   │   ├── logging.py        # Logging configuration
│   │   ├── security.py       # Security utilities
│   │   └── exceptions.py     # Custom exceptions
│   │
│   ├── middleware/            # Middleware components
│   │   ├── __init__.py
│   │   └── rate_limit.py     # Rate limiting
│   │
│   ├── models/                # Database models
│   │   ├── user.py
│   │   ├── system_user.py
│   │   ├── agent.py
│   │   ├── chat.py
│   │   ├── campaign.py
│   │   ├── call_log.py
│   │   ├── sip_trunk.py
│   │   ├── knowledge_document.py
│   │   └── knowledge_chunk.py
│   │
│   ├── repositories/          # Data access layer
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic
│   │   ├── agent_service.py
│   │   ├── analytics_service.py
│   │   ├── auth_service.py
│   │   ├── call_service.py
│   │   ├── chat_service.py
│   │   ├── email_service.py
│   │   ├── knowledge_service.py
│   │   ├── ollama_service.py
│   │   ├── rag_service.py
│   │   ├── sip_service.py
│   │   ├── stt_service.py
│   │   ├── whatsapp_service.py
│   │   └── ... (TTS services)
│   │
│   └── config/                # Configuration files
│
├── docs/                      # 📚 Documentation
│   ├── API.md                # API documentation
│   ├── DEPLOYMENT.md         # Deployment guide
│   ├── DEVELOPMENT.md        # Development guide
│   └── STRUCTURE.md          # This file
│
├── storage/                   # 💾 Storage directory
│   ├── cache/                # Cache files
│   ├── knowledge/            # Knowledge base documents
│   ├── media/                # Media files
│   │   └── tts/             # TTS audio files
│   └── uploads/              # User uploads
│
├── logs/                      # 📝 Application logs
│   └── archive/              # Archived logs
│
├── migrations/                # Database migrations
├── kani-tts/                 # KaniTTS service
├── modules/                   # Optional modules
│   ├── dermaccina/
│   └── sync-elevenlabs/
│
├── .env                       # Environment variables
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
├── init_db.py               # Database initialization
├── start.py                  # Server startup script
└── README.md                 # Main documentation
```

## 🔒 Security Features

### Authentication
- JWT-based authentication
- Bcrypt password hashing
- Token refresh mechanism
- Role-based access control (RBAC)

### API Protection
- Rate limiting (100 req/min default)
- CORS configuration
- Input validation with Pydantic
- SQL injection protection

### Data Security
- Environment variables for secrets
- Secure password storage
- Session management
- API key support

## 📊 Database Schema

### Core Tables
- `system_users` - Admin and system users
- `users` - WhatsApp users
- `agents` - AI agents
- `chat_sessions` - Chat sessions
- `messages` - Chat messages

### Feature Tables
- `campaigns` - Marketing campaigns
- `call_logs` - Call records
- `sip_trunks` - SIP configurations
- `knowledge_documents` - RAG documents
- `knowledge_chunks` - Document chunks with embeddings

## 🚀 Quick Start

### Initialize Database
```bash
python init_db.py
```

### Start Server
```bash
python start.py
```

### Default Admin Credentials
- **Email**: admin@eva.ai
- **Password**: admin123
- ⚠️ **Change immediately after first login!**

## 📁 Storage Organization

### Cache (`storage/cache/`)
- Embeddings cache
- Knowledge search cache
- Analytics cache
- Auto-cleanup enabled

### Knowledge Base (`storage/knowledge/`)
- Organized by agent ID
- Supports PDF, DOCX, TXT, MD
- Automatic chunking and indexing

### Media (`storage/media/`)
- TTS audio files
- Uploaded media
- Temporary files

## 📝 Logging

### Log Levels
- **INFO**: General information
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **DEBUG**: Debug information (dev only)

### Log Files
- `logs/app.log` - Main application log
- `logs/archive/` - Archived logs
- Automatic rotation (10MB max)

## 🔧 Configuration

### Environment Variables
All configuration in `.env` file:
- Application settings
- Database URL
- API keys (Ollama, Twilio, WhatsApp, etc.)
- Service URLs
- Security settings

### Feature Flags
- Debug mode
- CORS origins
- Rate limits
- Cache TTL values

## 📚 Documentation Files

- `README.md` - Main project documentation
- `docs/API.md` - API endpoints reference
- `docs/DEPLOYMENT.md` - Production deployment
- `docs/DEVELOPMENT.md` - Development setup
- `docs/STRUCTURE.md` - This file

## 🏗️ Architecture Principles

1. **Separation of Concerns**: Clear separation between layers
2. **Dependency Injection**: Services use dependency injection
3. **Repository Pattern**: Data access abstraction
4. **Service Layer**: Business logic isolation
5. **Middleware**: Cross-cutting concerns
6. **Caching**: Performance optimization
7. **Rate Limiting**: API protection

## 🎯 Best Practices

### Code Organization
- One responsibility per file
- Clear naming conventions
- Type hints everywhere
- Comprehensive docstrings

### Security
- Never commit `.env` files
- Use environment variables
- Validate all inputs
- Sanitize outputs

### Performance
- Use caching where appropriate
- Async operations for I/O
- Database query optimization
- Connection pooling

---

**Last Updated**: December 2025  
**Version**: 3.0.0
