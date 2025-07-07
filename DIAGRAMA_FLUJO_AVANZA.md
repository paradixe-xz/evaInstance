# 🔄 Diagrama de Flujo Completo - AVANZA

## 📊 Flujo Principal del Sistema

```mermaid
flowchart TD
    A[📊 Subir Excel con Contactos] --> B[📱 Enviar Mensaje WhatsApp Inicial]
    B --> C{Usuario Responde}
    
    C -->|"SÍ / Me interesa"| D[📞 Programar Llamada Inmediata]
    C -->|"NO / No me interesa"| E[🤖 IA Convence]
    C -->|"Respuesta no clara"| F[❓ Pide Clarificación]
    
    E --> G{Usuario Cambia de Opinión?}
    G -->|"SÍ"| D
    G -->|"NO"| H[🔄 Seguir Convenciendo]
    H --> G
    
    F --> C
    
    D --> I[🎤 Llamada Telefónica con Ana]
    I --> J[📝 Transcripción Completa]
    J --> K[🧠 Análisis IA de la Llamada]
    K --> L[📱 Pregunta Post-Llamada]
    
    L --> M{Usuario Interesado?}
    M -->|"SÍ / Quiero proceder"| N[📄 Solicitar Documentos]
    M -->|"NO"| O[💬 Ofrecer Promociones Futuras]
    
    N --> P[📋 Documentos Requeridos]
    P --> Q[✅ Verificar Nombres]
    
    Q -->|"Nombres Coinciden"| R[📧 Enviar por Email]
    Q -->|"Nombres NO Coinciden"| S[❌ Pedir Corrección]
    
    R --> T[🎉 Proceso Completado]
    S --> N
    
    O --> U[📊 Registrar No Interesado]
    
    style A fill:#e1f5fe
    style T fill:#c8e6c9
    style U fill:#ffcdd2
```

## 🎯 Estados de Conversación Detallados

```mermaid
stateDiagram-v2
    [*] --> initial: Primer contacto
    
    initial --> waiting_confirmation: Envía mensaje inicial
    
    waiting_confirmation --> scheduled_call: Usuario dice "SÍ"
    waiting_confirmation --> convincing: Usuario dice "NO"
    waiting_confirmation --> waiting_confirmation: Respuesta no clara
    
    convincing --> scheduled_call: Usuario cambia de opinión
    convincing --> convincing: Continúa convenciendo
    
    scheduled_call --> call_completed: Llamada termina
    
    call_completed --> waiting_documents: Usuario interesado
    call_completed --> not_interested: Usuario no interesado
    
    waiting_documents --> documents_received: Documentos enviados
    documents_received --> documents_verified: Nombres coinciden
    documents_received --> waiting_documents: Nombres NO coinciden
    
    documents_verified --> [*]: Proceso completado
    not_interested --> [*]: No interesado
    
    note right of initial
        📱 Mensaje de bienvenida
        Presentación de AVANZA
    end note
    
    note right of waiting_confirmation
        🤔 Esperando respuesta
        SÍ = Llamada inmediata
        NO = IA convence
    end note
    
    note right of convincing
        🎯 IA persuasiva
        Argumentos financieros
        Casos de éxito
    end note
    
    note right of scheduled_call
        📞 Llamada automática
        Ana + IA conversan
        Transcripción completa
    end note
    
    note right of call_completed
        🧠 Análisis IA
        Verificar interés
        Preguntar si procede
    end note
    
    note right of waiting_documents
        📄 Solicitar:
        • Cédula
        • Recibo de pago
        • Formato autorización
    end note
    
    note right of documents_verified
        ✅ Verificación exitosa
        📧 Envío por email
        🎉 Proceso completado
    end note
```

## 📱 Flujo de Mensajes WhatsApp

```mermaid
sequenceDiagram
    participant S as Sistema
    participant U as Usuario
    participant IA as IA Ana
    participant T as Twilio
    participant E as Email
    
    S->>U: 🎧 Mensaje inicial AVANZA
    U->>S: "SÍ" o "NO"
    
    alt Usuario dice "SÍ"
        S->>T: Programar llamada
        T->>U: Llamada telefónica
        U->>T: Conversación con Ana
        T->>S: Transcripción
        S->>IA: Analizar conversación
        IA->>S: Análisis de interés
        S->>U: ¿Te interesó la propuesta?
        
        alt Usuario interesado
            U->>S: "SÍ, quiero proceder"
            S->>U: 📄 Solicitar documentos
            U->>S: Enviar cédula + recibo
            S->>S: Verificar nombres
            S->>E: Enviar por email
            E->>S: Confirmación
            S->>U: ✅ Proceso completado
        else Usuario no interesado
            U->>S: "NO"
            S->>U: 💬 Ofrecer promociones
        end
        
    else Usuario dice "NO"
        S->>IA: Activar modo persuasivo
        IA->>S: Argumentos convincentes
        S->>U: 🎯 Mensaje persuasivo
        U->>S: Nueva respuesta
        
        alt Usuario convence
            S->>T: Programar llamada
            Note over S,T: Continuar flujo normal
        else Usuario sigue negando
            S->>IA: Más argumentos
            IA->>S: Persistir
            S->>U: 🔄 Seguir convenciendo
        end
    end
```

## 🔧 Arquitectura del Sistema

```mermaid
graph TB
    subgraph "Frontend/API"
        A[FastAPI Server]
        B[WhatsApp Business API]
        C[Twilio API]
        D[ElevenLabs API]
    end
    
    subgraph "Procesamiento"
        E[IA Ana - Ollama]
        F[Análisis de Transcripciones]
        G[Verificación de Documentos]
        H[Envio de Emails]
    end
    
    subgraph "Almacenamiento"
        I[Conversaciones JSON]
        J[Transcripciones]
        K[Análisis IA]
        L[Archivos de Audio]
    end
    
    subgraph "Integraciones"
        M[WhatsApp Business]
        N[Twilio Voice]
        O[Gmail SMTP]
        P[Ollama Local]
    end
    
    A --> B
    A --> C
    A --> D
    A --> E
    A --> F
    A --> G
    A --> H
    
    F --> I
    F --> J
    F --> K
    D --> L
    
    B --> M
    C --> N
    H --> O
    E --> P
    
    style A fill:#ff9800
    style E fill:#4caf50
    style M fill:#25d366
    style N fill:#f44336
```

## 📊 Métricas y Estados

```mermaid
pie title Estados de Conversación
    "waiting_confirmation" : 25
    "convincing" : 20
    "scheduled_call" : 15
    "call_completed" : 15
    "waiting_documents" : 10
    "documents_verified" : 10
    "not_interested" : 5
```

## 🎯 Puntos de Decisión Clave

```mermaid
graph LR
    A[Contacto Inicial] --> B{Responde WhatsApp?}
    B -->|SÍ| C[Interesado Inmediato]
    B -->|NO| D[IA Convence]
    
    C --> E[Llamada Programada]
    D --> F{Convence IA?}
    F -->|SÍ| E
    F -->|NO| G[Persistir]
    G --> F
    
    E --> H[Llamada Realizada]
    H --> I{Interesado Post-Llamada?}
    I -->|SÍ| J[Solicitar Documentos]
    I -->|NO| K[No Interesado]
    
    J --> L{Documentos Correctos?}
    L -->|SÍ| M[Enviar por Email]
    L -->|NO| N[Pedir Corrección]
    N --> J
    
    M --> O[Proceso Exitoso]
    K --> P[Registrar No Interesado]
    
    style O fill:#4caf50
    style P fill:#f44336
    style M fill:#2196f3
```

## 🔄 Flujo de Datos

```mermaid
flowchart LR
    A[Excel Contactos] --> B[API FastAPI]
    B --> C[WhatsApp Business]
    B --> D[Twilio Voice]
    
    C --> E[Webhook]
    D --> F[Transcripción]
    
    E --> G[Procesamiento IA]
    F --> G
    
    G --> H[Análisis]
    H --> I[Decisión]
    
    I --> J[Documentos]
    J --> K[Verificación]
    K --> L[Email]
    
    style A fill:#e3f2fd
    style L fill:#c8e6c9
    style G fill:#fff3e0
```

---

## 📋 Resumen del Flujo Completo

### **Fase 1: Contacto Inicial**
1. 📊 Subir Excel con contactos
2. 📱 Enviar mensaje WhatsApp personalizado
3. 🤖 Procesar respuesta del usuario

### **Fase 2: Persuasión Inteligente**
1. 🎯 Si dice "NO" → IA convence
2. 🔄 Persistencia hasta convencer
3. 📞 Programar llamada cuando acepte

### **Fase 3: Llamada Telefónica**
1. 🎤 Ana habla con IA en tiempo real
2. 📝 Transcripción completa
3. 🧠 Análisis automático con IA

### **Fase 4: Seguimiento Post-Llamada**
1. 📱 Preguntar si se interesó
2. 📄 Solicitar documentos si dice "SÍ"
3. ✅ Verificar nombres en documentos

### **Fase 5: Finalización**
1. 📧 Enviar por correo si coinciden
2. 🎉 Proceso completado
3. 📊 Registrar métricas

**¡El sistema está completamente automatizado y optimizado para máxima conversión!** 🚀 