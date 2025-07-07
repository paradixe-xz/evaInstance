# 🚀 Flujo Completo AVANZA - WhatsApp + IA + Llamadas + Documentos

## 📋 Resumen del Nuevo Flujo

**Flujo implementado:**

1. **📱 Mensaje inicial WhatsApp** → Usuario recibe presentación
2. **🤖 IA convence** → Si dice "NO", IA lo convence
3. **📞 Llamada telefónica** → Si acepta, se programa llamada
4. **🎯 Verificación post-llamada** → Pregunta si se interesó
5. **📄 Solicitud de documentos** → Cédula y recibo de pago
6. **✅ Verificación de nombres** → Compara nombres en documentos
7. **📧 Envío por correo** → Si coinciden, envía por email

---

## 🔄 Flujo Detallado por Etapas

### **ETAPA 1: Mensaje Inicial**
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

### **ETAPA 2: Respuesta del Usuario**

#### **Si dice "SÍ":**
```
✅ ¡Excelente Juan! 

Tu llamada está programada. Te llamaré puntualmente para revisar tu elegibilidad y explicarte todos los beneficios del préstamo AVANZA.

📋 En la llamada de 10 minutos revisaremos:
• Tu situación actual y capacidad de pago
• Cómo podemos bajarte esa cuota que te tiene apretado
• Monto que puedes obtener (hasta $150 millones)
• Documentación necesaria (solo cédula vigente)
• Proceso de desembolso (24-48 horas)

📞 Llamada programada. Te llamaré en 1 minuto.
```

#### **Si dice "NO":**
```
Entiendo tu preocupación Juan, pero déjame explicarte algo importante:

¿Sabías que con nuestros préstamos puedes:
• Reducir tus cuotas mensuales hasta en un 40%
• Recibir hasta $150 millones sin codeudor
• Tener descuento directo por nómina (sin olvidos)
• Aprobación en 24-48 horas

Muchos de nuestros clientes han logrado ahorrar más de $500,000 mensuales. ¿Te parece que vale la pena que te explique cómo? Solo necesito 5 minutos de tu tiempo.

¿Me das esa oportunidad? 💰
```

### **ETAPA 3: Conversación Persuasiva**
Si el usuario sigue diciendo "NO", la IA continúa convenciendo:

```
Entiendo Juan, pero déjame contarte algo:

María, una docente como tú, logró reducir su cuota de $800,000 a $450,000 mensuales. Eso significa $350,000 más en su bolsillo cada mes.

¿Te imaginas qué podrías hacer con ese dinero extra? Pagar deudas, ahorrar, o simplemente vivir más tranquila.

¿Vale la pena que te explique cómo? Solo 5 minutos. 💰
```

### **ETAPA 4: Llamada Telefónica**
- **Sistema llama automáticamente**
- **Ana habla con IA** (guion de 10 minutos)
- **Transcripción completa** de la conversación
- **Análisis automático** con IA

### **ETAPA 5: Verificación Post-Llamada**
Después de la llamada, el sistema pregunta:

```
🎉 ¡Excelente Juan! 

Perfecto, para continuar con tu solicitud necesito que me envíes estos documentos:

📋 Documentos requeridos:
1. 📄 Cédula de ciudadanía (frente y reverso)
2. 💰 Último recibo de pago de nómina
3. 📝 Formato de autorización (te lo envío ahora)

📱 Envíalos por WhatsApp a este mismo número
📧 O por email a: info@avanza.lat

¿Tienes estos documentos a la mano? 📄
```

### **ETAPA 6: Recepción de Documentos**
El usuario envía los documentos y el sistema:

1. **Verifica nombres** → Compara nombre en cédula vs recibo
2. **Si coinciden** → Envía por correo electrónico
3. **Si no coinciden** → Pide corrección

#### **Respuesta si coinciden:**
```
✅ ¡Perfecto Juan! 

He verificado tus documentos y los nombres coinciden perfectamente.

📧 He enviado tus documentos por correo electrónico.

📋 Próximos pasos:
1. ✅ Documentos verificados
2. 📊 Evaluación financiera en proceso
3. 📞 Confirmación de aprobación (24-48 horas)
4. 💰 Desembolso directo a tu cuenta

Te mantendré informado del proceso. ¡Gracias por confiar en AVANZA! 🎉
```

#### **Respuesta si NO coinciden:**
```
❌ Juan, he detectado una diferencia en los nombres de los documentos.

Por favor verifica que:
• El nombre en la cédula sea exactamente igual al del recibo de pago
• Los documentos estén legibles y completos

Una vez corregido, envíalos nuevamente. 📄
```

---

## 🎯 Estados de Conversación Implementados

| Estado | Descripción | Acción del Sistema |
|--------|-------------|-------------------|
| `initial` | Primer contacto | Envía mensaje de bienvenida |
| `waiting_confirmation` | Esperando respuesta | Procesa "SÍ/NO" |
| `convincing` | Usuario dijo "NO" | IA lo convence |
| `scheduled_call` | Llamada programada | Inicia llamada automática |
| `call_completed` | Llamada terminada | Pregunta si se interesó |
| `waiting_documents` | Esperando documentos | Solicita cédula y recibo |
| `documents_received` | Documentos recibidos | Procesa documentos |
| `documents_verified` | Documentos verificados | Envía por correo |
| `not_interested` | No interesado | Ofrece promociones |

---

## 🔧 Endpoints Implementados

### **Envío Combinado (WhatsApp + Llamada)**
```bash
POST /sendNumbers
# Envía WhatsApp + programa llamada
```

### **Solo WhatsApp**
```bash
POST /sendWhatsAppOnly
# Solo envía mensajes WhatsApp
```

### **Webhook (Recepción Automática)**
```bash
POST /whatsapp/business/webhook
# Recibe mensajes y responde automáticamente
```

### **Procesamiento de Documentos**
```bash
POST /whatsapp/documents
# Recibe y verifica documentos
```

---

## 📊 Variables de Entorno Necesarias

```bash
# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=tu_access_token_aqui
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id_aqui
WHATSAPP_BUSINESS_ACCOUNT_ID=tu_business_account_id_aqui
WHATSAPP_VERIFY_TOKEN=tu_verify_token_aqui
WHATSAPP_WEBHOOK_SECRET=tu_webhook_secret_aqui

# Twilio (para llamadas)
TWILIO_ACCOUNT_SID=tu_account_sid
TWILIO_AUTH_TOKEN=tu_auth_token
TWILIO_PHONE_NUMBER=tu_phone_number
TWILIO_WEBHOOK_URL=tu_webhook_url

# ElevenLabs (para audio)
ELEVENLABS_API_KEY=tu_api_key
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Email (para envío de documentos)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=tu_email@gmail.com
EMAIL_PASSWORD=tu_password_app
```

---

## 🎯 **Ventajas del Nuevo Flujo**

1. **✅ Persuasión inteligente** - IA convence si dice "NO"
2. **✅ Doble canal** - WhatsApp + llamada telefónica
3. **✅ Verificación automática** - Compara nombres en documentos
4. **✅ Envío por correo** - Automático si coinciden
5. **✅ Seguimiento completo** - Todo el proceso registrado
6. **✅ Menos intrusivo** - Usuario decide cuándo llamar
7. **✅ Conversación natural** - IA responde en tiempo real

---

## 🚀 **Para Usar:**

1. **Configura las variables de entorno** en tu `.env`
2. **Sube archivo Excel** con contactos (`/sendNumbers`)
3. **Sistema envía WhatsApp** automáticamente
4. **IA convence** si es necesario
5. **Llamada telefónica** si acepta
6. **Solicita documentos** post-llamada
7. **Verifica y envía** por correo

**¡El flujo completo está implementado y funcionando!** 🎉 