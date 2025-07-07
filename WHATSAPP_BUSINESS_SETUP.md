# 📱 WhatsApp Business API - Configuración Completa

## 🔧 Variables de Entorno Requeridas

Agrega estas variables a tu archivo `.env`:

```bash
# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=tu_access_token_aqui
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id_aqui
WHATSAPP_BUSINESS_ACCOUNT_ID=tu_business_account_id_aqui
WHATSAPP_VERIFY_TOKEN=tu_verify_token_aqui
WHATSAPP_WEBHOOK_SECRET=tu_webhook_secret_aqui

# Twilio (mantener para llamadas telefónicas)
TWILIO_ACCOUNT_SID=tu_account_sid
TWILIO_AUTH_TOKEN=tu_auth_token
TWILIO_PHONE_NUMBER=tu_phone_number
TWILIO_WEBHOOK_URL=tu_webhook_url

# ElevenLabs (para audio)
ELEVENLABS_API_KEY=tu_api_key
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# URL pública para archivos de audio
PUBLIC_BASE_URL=tu_url_publica
```

## 🚀 Endpoints Implementados

### 1. Envío de Mensajes

#### POST `/send_whatsapp`
Envía mensaje individual usando WhatsApp Business API

```bash
curl -X POST "http://localhost:4000/send_whatsapp" \
  -F "to=+573001234567" \
  -F "message=Hola, soy Ana de AVANZA" \
  -F "name=Juan"
```

#### POST `/whatsapp/business/send`
Endpoint específico para WhatsApp Business API con soporte para plantillas

```bash
# Mensaje de texto
curl -X POST "http://localhost:4000/whatsapp/business/send" \
  -F "to=+573001234567" \
  -F "message=Hola desde WhatsApp Business API"

# Plantilla
curl -X POST "http://localhost:4000/whatsapp/business/send" \
  -F "to=+573001234567" \
  -F "template_name=hello_world" \
  -F "language_code=es"
```

### 2. Envío Masivo

#### POST `/whatsapp/bulk_send`
Envía mensajes masivos desde archivo Excel

```bash
curl -X POST "http://localhost:4000/whatsapp/bulk_send" \
  -F "file=@contactos_whatsapp.xlsx"
```

**Formato del archivo Excel:**
| numero        | mensaje                    | nombre |
|---------------|----------------------------|--------|
| +573001234567 | Hola Juan, soy Ana...     | Juan   |
| +573007654321 | Hola María, soy Ana...    | María  |

### 3. Webhook para Recepción

#### POST `/whatsapp/business/webhook`
Webhook para recibir mensajes automáticamente

**Configurar en Meta Developer Console:**
```
https://tu-dominio.com/whatsapp/business/webhook
```

### 4. Información y Plantillas

#### GET `/whatsapp/business/info`
Obtiene información del número de WhatsApp Business

```bash
curl "http://localhost:4000/whatsapp/business/info"
```

#### GET `/whatsapp/business/templates`
Obtiene plantillas disponibles

```bash
curl "http://localhost:4000/whatsapp/business/templates"
```

## 🤖 Flujo de Conversación Automática

### Estados de Conversación:

1. **`initial`** - Primer contacto
   - Envía presentación de AVANZA
   - Pregunta si puede llamar

2. **`waiting_confirmation`** - Esperando respuesta
   - Si dice "SÍ" → Programa llamada inmediata
   - Si dice "NO" → Ofrece programar para después
   - Si no es claro → Pide clarificación

3. **`waiting_schedule`** - Usuario quiere programar
   - Si dice "ahora" → Llamada inmediata
   - Si da hora específica → Programa para esa hora

4. **`scheduled_call`** - Llamada programada
   - Confirma programación
   - Inicia llamada automática

## 📊 Ejemplo de Respuestas

### Mensaje de Bienvenida:
```
🎧 ¡Hola Juan! Soy ANA de AVANZA 💼

No te estoy escribiendo para venderte un crédito —te lo prometo—, sino para ayudarte a organizar tus finanzas, que es algo que todos necesitamos hoy en día.

📌 Tenemos tasas desde solo **1.6% mensual** por libranza
📌 Montos hasta $150 millones sin codeudor
📌 Sin importar si estás reportado en centrales
📌 Descuento directo de nómina

¿Puedo llamarte para explicártelo? No es una llamada comercial, es una charla entre tú y yo buscando la mejor forma de que el dinero te rinda más sin estrés.

¿Qué prefieres? 💰💪
```

## 🔍 Monitoreo y Debugging

### Ver logs en tiempo real:
```bash
tail -f nohup.out
```

### Verificar estado de conversaciones:
```bash
curl "http://localhost:4000/conversations/status"
```

### Probar envío manual:
```bash
curl -X POST "http://localhost:4000/send_whatsapp" \
  -F "to=+573001234567" \
  -F "message=Prueba desde API" \
  -F "name=Test"
```

## ⚠️ Consideraciones Importantes

### 1. Rate Limits
- WhatsApp Business API tiene límites estrictos
- Máximo 1000 mensajes/día en desarrollo
- Pausa de 1 segundo entre mensajes masivos

### 2. Números de WhatsApp
- Solo números verificados por WhatsApp Business
- Formato: +573001234567 (con código de país)

### 3. Mensajes
- Máximo 1024 caracteres por mensaje
- Soporte para emojis y formato básico
- No soporta HTML complejo

### 4. Plantillas
- Deben ser aprobadas por Meta
- Solo para mensajes de marketing
- Requieren botones de opt-out

## 🚀 Configuración en Meta Developer Console

### 1. Crear App en Meta
1. Ve a [developers.facebook.com](https://developers.facebook.com)
2. Crea una nueva app
3. Agrega producto "WhatsApp"

### 2. Configurar WhatsApp Business API
1. Ve a "WhatsApp" → "Getting Started"
2. Configura tu número de teléfono
3. Obtén las credenciales necesarias

### 3. Configurar Webhook
1. Ve a "Webhooks"
2. Agrega URL: `https://tu-dominio.com/whatsapp/business/webhook`
3. Verifica el webhook

### 4. Obtener Credenciales
```bash
# Access Token
WHATSAPP_ACCESS_TOKEN=EAAG...

# Phone Number ID
WHATSAPP_PHONE_NUMBER_ID=123456789

# Business Account ID
WHATSAPP_BUSINESS_ACCOUNT_ID=987654321

# Verify Token (crear uno personalizado)
WHATSAPP_VERIFY_TOKEN=mi_token_secreto_123

# Webhook Secret (opcional)
WHATSAPP_WEBHOOK_SECRET=mi_secreto_webhook
```

## 🔧 Troubleshooting

### Error: "Invalid phone number"
- Verificar formato: debe ser +573001234567
- Asegurar que el número esté verificado en WhatsApp Business

### Error: "Webhook not responding"
- Verificar que el servidor esté corriendo
- Verificar URL del webhook en Meta Console
- Verificar logs del servidor

### Error: "Rate limit exceeded"
- Reducir velocidad de envío masivo
- Implementar cola de mensajes
- Usar delays entre envíos

### Error: "Access token invalid"
- Verificar que el token esté actualizado
- Verificar permisos de la app
- Regenerar token si es necesario

## 📈 Próximos Pasos

1. **Configurar plantillas aprobadas**
2. **Implementar análisis de sentimientos**
3. **Agregar soporte para media (imágenes, documentos)**
4. **Integrar con CRM**
5. **Implementar métricas avanzadas**

## 🎯 Ventajas de WhatsApp Business API

### ✅ Pros:
- Usa tu propio número de WhatsApp
- Sin límites de sandbox
- Mejor integración con WhatsApp
- Soporte para plantillas aprobadas
- Métricas detalladas

### ⚠️ Contras:
- Proceso de aprobación complejo
- Costos asociados
- Requiere verificación de Meta
- Configuración más compleja

## 📧 Configuración de Email (Para Envío de Documentos)

### Variables de Entorno para Email:
```bash
# Email (para envío de documentos)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=tu_email@gmail.com
EMAIL_PASSWORD=tu_password_app
```

### Configurar Gmail:
1. Activar autenticación de 2 factores
2. Generar contraseña de aplicación
3. Usar esa contraseña en EMAIL_PASSWORD

---

**Nota:** Esta implementación usa WhatsApp Business API oficial de Meta. Para uso en producción, necesitarás aprobación de Meta y configuración completa de la app. 