# API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

All protected endpoints require JWT authentication.

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "admin@eva.ai",
  "password": "admin123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@eva.ai",
    "username": "admin"
  }
}
```

### Using Authentication
```http
Authorization: Bearer {access_token}
```

---

## 📊 Analytics Endpoints

### Get Dashboard Metrics
```http
GET /analytics/dashboard?days=30
Authorization: Bearer {token}

Response:
{
  "period_days": 30,
  "agents": {
    "total": 5,
    "active": 3,
    "inactive": 2
  },
  "conversations": {
    "total_sessions": 150,
    "total_messages": 1200,
    "avg_messages_per_session": 8.0
  },
  "calls": {
    "total": 45,
    "avg_duration_seconds": 180.5
  },
  "campaigns": {
    "total": 3,
    "active": 2,
    "paused": 1
  }
}
```

### Get Agent Performance
```http
GET /analytics/agents/{agent_id}/performance?days=30
Authorization: Bearer {token}
```

### Get Campaign Analytics
```http
GET /analytics/campaigns/{campaign_id}
Authorization: Bearer {token}
```

---

## 🏥 Health Check Endpoints

### Basic Health
```http
GET /health

Response:
{
  "status": "healthy",
  "service": "Eva AI Assistant"
}
```

### Detailed Health
```http
GET /health/detailed

Response:
{
  "status": "healthy",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful"
    },
    "ollama": {
      "status": "healthy",
      "message": "Ollama is running",
      "models_count": 3
    },
    "disk_space": {
      "status": "healthy",
      "free_gb": 50,
      "total_gb": 500,
      "usage_percent": 90.0
    },
    "memory": {
      "status": "healthy",
      "total_gb": 16.0,
      "available_gb": 8.0,
      "usage_percent": 50.0
    }
  }
}
```

---

## 🔗 Webhooks Endpoints

### List Webhooks
```http
GET /webhooks/
Authorization: Bearer {token}
```

### Create Webhook
```http
POST /webhooks/
Authorization: Bearer {token}
Content-Type: application/json

{
  "url": "https://example.com/webhook",
  "events": ["message.received", "call.ended"],
  "description": "My webhook",
  "secret": "optional-secret",
  "active": true
}
```

### Test Webhook
```http
POST /webhooks/{webhook_id}/test
Authorization: Bearer {token}
```

### Get Webhook Logs
```http
GET /webhooks/{webhook_id}/logs?limit=50
Authorization: Bearer {token}
```

---

## 🤖 Agents Endpoints

### Create Agent
```http
POST /agents/ollama/create
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Sales Assistant",
  "base_model": "llama2",
  "system_prompt": "You are a helpful sales assistant...",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

### List Agents
```http
GET /agents/
Authorization: Bearer {token}
```

### Chat with Agent (Streaming)
```http
POST /agents/ollama/{agent_id}/chat/stream
Authorization: Bearer {token}
Content-Type: application/json

{
  "message": "Hello, how can you help me?",
  "session_id": "session-123",
  "use_knowledge_base": true
}

Response: Server-Sent Events (SSE)
```

---

## 📚 Knowledge Base Endpoints

### Upload Document
```http
POST /knowledge/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

agent_id: 1
file: document.pdf
title: "Product Manual"
description: "Complete product documentation"
```

### Search Knowledge Base
```http
POST /knowledge/search
Authorization: Bearer {token}
Content-Type: application/json

{
  "agent_id": 1,
  "query": "What is the product warranty?",
  "limit": 5,
  "threshold": 0.7
}

Response:
{
  "results": [
    {
      "chunk_id": 123,
      "content": "The product warranty is 2 years...",
      "similarity": 0.89,
      "document_title": "Product Manual",
      "page": 15
    }
  ]
}
```

### Get Knowledge Stats
```http
GET /knowledge/stats?agent_id=1
Authorization: Bearer {token}
```

---

## 📊 Campaigns Endpoints

### List Campaigns
```http
GET /campaigns/?skip=0&limit=100
Authorization: Bearer {token}
```

### Create Campaign
```http
POST /campaigns/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Summer Campaign",
  "slug": "summer-2024",
  "type": "whatsapp",
  "description": "Summer promotion campaign",
  "status": "draft"
}
```

### Start Campaign
```http
POST /campaigns/{campaign_id}/start
Authorization: Bearer {token}
```

### Stop Campaign
```http
POST /campaigns/{campaign_id}/stop
Authorization: Bearer {token}
```

---

## 💬 WhatsApp Endpoints

### Send Message
```http
POST /whatsapp/send-message
Authorization: Bearer {token}
Content-Type: application/json

{
  "to": "+1234567890",
  "message": "Hello from Eva AI!"
}
```

### Webhook (Receive Messages)
```http
POST /whatsapp/webhook
Content-Type: application/json

# WhatsApp will send messages here
# Automatic AI response enabled
```

---

## 📞 Calls Endpoints

### Transcribe Audio
```http
POST /calls/stt/transcribe
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: audio.wav
language: es-ES
```

### Generate TTS Audio
```http
POST /calls/tts/generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "text": "Hello, welcome to Eva AI Assistant",
  "language": "es",
  "engine": "kanitts"
}

Response: Audio file (WAV)
```

### Get Call Logs
```http
GET /calls/logs?limit=100&offset=0
Authorization: Bearer {token}
```

---

## 📧 Email Endpoints

### Send Email
```http
POST /email/send
Authorization: Bearer {token}
Content-Type: application/json

{
  "to": "user@example.com",
  "subject": "Welcome",
  "text": "Thank you for contacting us",
  "html": "<p>Thank you for contacting us</p>"
}
```

---

## 📡 SIP Trunk Endpoints

### Create SIP Trunk
```http
POST /sip/trunks
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Main SIP Trunk",
  "host": "sip.provider.com",
  "port": 5060,
  "username": "user",
  "password": "pass",
  "protocol": "UDP",
  "enabled": true
}
```

### Get SIP Trunk Status
```http
GET /sip/trunks/{trunk_id}/status
Authorization: Bearer {token}
```

---

## 🔄 Rate Limiting

All endpoints are rate-limited:

- **Default**: 100 requests/minute
- **Auth**: 5 requests/minute
- **Chat**: 30 requests/minute
- **Analytics**: 20 requests/minute
- **Knowledge**: 10 requests/minute

Response headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Window: 60
```

When limit exceeded:
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 30

{
  "detail": "Rate limit exceeded",
  "retry_after": 30
}
```

---

## 📝 Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error",
  "error_code": "VALIDATION_ERROR"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 30
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "error_code": "INTERNAL_ERROR"
}
```

---

## 🔧 Interactive Documentation

Visit these URLs when server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

**Last Updated**: December 2025  
**API Version**: v1
