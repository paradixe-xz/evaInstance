# 🤖 Flujo Completo: WhatsApp + IA + Llamadas

## 📋 Resumen del Proceso

**SÍ, exactamente así funciona:**

1. **Subes archivo Excel** con contactos
2. **Sistema envía mensaje WhatsApp** a cada número
3. **Usuario responde** en WhatsApp
4. **IA procesa la respuesta** y genera respuesta automática
5. **Si acepta llamada** → Se programa llamada telefónica
6. **Conversación continua** hasta que se complete

---

## 🔄 Flujo Detallado

### 1. **Inicio del Proceso**

```bash
# Subir archivo Excel con contactos
curl -X POST "http://localhost:4000/sendNumbers" \
  -F "file=@contactos.xlsx"
```

**Archivo Excel:**
| numero        | nombre |
|---------------|--------|
| +573001234567 | Juan   |
| +573007654321 | María  |

### 2. **Envío Automático de WhatsApp**

Para cada contacto, el sistema:

1. **Envía mensaje inicial:**
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

2. **Programa llamada telefónica** (como respaldo)

### 3. **Conversación con IA**

Cuando el usuario responde en WhatsApp:

#### **Escenario A: Usuario dice "SÍ"**
```
Usuario: "Sí, me interesa"
IA: "🎯 ¡Perfecto Juan! 

Para agendar tu llamada y revisar tu elegibilidad para el préstamo AVANZA, dime cuándo te parece mejor:

⏰ Opciones:
• "Ahora mismo" - Te llamo en 10 minutos
• "En 2 horas" - Te llamo en 2 horas  
• "A las 3:30 PM" - Te llamo a esa hora
• "Mañana a las 10:00" - Te llamo mañana

¿Cuándo te viene mejor para revisar tu situación y calcular tu préstamo? 💰"
```

#### **Escenario B: Usuario dice "NO"**
```
Usuario: "No, ahora no"
IA: "Entiendo perfectamente. ¿Cuándo te vendría mejor que te llame?

⏰ Opciones:
• En 2 horas
• Mañana a las 10:00
• El viernes a las 3:00 PM

O simplemente dime 'ahora' cuando estés listo."
```

#### **Escenario C: Usuario dice "Ahora"**
```
Usuario: "Ahora"
IA: "✅ ¡Excelente Juan! 

Tu llamada está programada. Te llamaré puntualmente para revisar tu elegibilidad y explicarte todos los beneficios del préstamo AVANZA.

📋 En la llamada de 10 minutos revisaremos:
• Tu situación actual y capacidad de pago
• Cómo podemos bajarte esa cuota que te tiene apretado
• Monto que puedes obtener (hasta $150 millones)
• Documentación necesaria (solo cédula vigente)
• Proceso de desembolso (24-48 horas)

📞 Llamada programada. Te llamaré en 1 minuto."
```

### 4. **Llamada Telefónica (Si Acepta)**

- **Sistema llama automáticamente**
- **Ana habla con IA** (guion de 10 minutos)
- **Transcripción completa** de la conversación
- **Análisis automático** con IA
- **Determina si necesita seguimiento humano**

---

## 🎯 Estados de Conversación

| Estado | Descripción | Acción del Sistema |
|--------|-------------|-------------------|
| `initial` | Primer contacto | Envía mensaje de bienvenida |
| `waiting_confirmation` | Esperando respuesta | Procesa "SÍ/NO" |
| `waiting_schedule` | Usuario quiere programar | Ofrece opciones de hora |
| `scheduled_call` | Llamada programada | Inicia llamada automática |
| `call_completed` | Llamada terminada | Analiza transcripción |
| `ready_for_human` | Necesita seguimiento | Notifica a humano |

---

## 📊 Ejemplo de Respuesta del Sistema

```json
{
  "message": "Procesamiento completado. 2 contactos procesados.",
  "total_contacts": 2,
  "valid_contacts": 2,
  "invalid_contacts": 0,
  "results": [
    {
      "numero": "+573001234567",
      "nombre": "Juan",
      "status": "whatsapp_y_llamada_programados",
      "whatsapp_message_id": "wamid.123456789",
      "call_sid": "CA123456789"
    },
    {
      "numero": "+573007654321",
      "nombre": "María",
      "status": "whatsapp_enviado",
      "whatsapp_message_id": "wamid.987654321",
      "call_sid": null
    }
  ]
}
```

---

## 🔧 Endpoints Disponibles

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

### **Envío Individual**
```bash
POST /send_whatsapp
# Envía un mensaje individual
```

### **Webhook (Recepción)**
```bash
POST /whatsapp/business/webhook
# Recibe mensajes y responde automáticamente
```

---

## ✅ **Respuesta a tu Pregunta**

**SÍ, exactamente así funciona:**

1. **Subes archivo Excel** → Sistema envía WhatsApp a cada número
2. **Usuario recibe mensaje** → Puede responder en WhatsApp
3. **IA procesa respuesta** → Genera respuesta automática
4. **Conversación continúa** → Hasta que acepte llamada
5. **Si acepta** → Se programa llamada telefónica automática

**El usuario puede hablar con la IA completamente por WhatsApp** antes de que se haga la llamada telefónica.

---

## 🎯 **Ventajas de este Enfoque**

1. **✅ Contacto inmediato** - WhatsApp llega instantáneamente
2. **✅ Conversación natural** - IA responde en tiempo real
3. **✅ Menos intrusivo** - Usuario decide cuándo llamar
4. **✅ Doble canal** - WhatsApp + llamada telefónica
5. **✅ Análisis completo** - Toda la conversación se registra

**¡El usuario puede tener una conversación completa con la IA por WhatsApp antes de decidir si quiere una llamada!** 