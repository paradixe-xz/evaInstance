from fastapi import FastAPI, HTTPException, Request, Form, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import subprocess
from twilio.rest import Client
from fastapi.responses import Response, PlainTextResponse
from twilio.twiml.voice_response import VoiceResponse
import ollama  # Para usar el modelo de chat
import requests
import speech_recognition as sr
from pydub import AudioSegment
import uuid
from fastapi.staticfiles import StaticFiles
import wave
from elevenlabs import ElevenLabs
import pandas as pd
import io
import pytz
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import json
import re
import asyncio
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()

# Configuración de zona horaria (Barranquilla, Colombia)
TIMEZONE = pytz.timezone('America/Bogota')  # Barranquilla usa la misma zona que Bogotá

# Twilio config (solo variables de entorno, sin valores hardcodeados)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')
TWILIO_WEBHOOK_URL = os.getenv('TWILIO_WEBHOOK_URL')

# WhatsApp Business API config
from .whatsappBusiness import whatsapp_business

# ElevenLabs config
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')  # Rachel voice

# Initialize ElevenLabs client
elevenlabs_client = None
if ELEVENLABS_API_KEY:
    elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Scheduler para programar llamadas
scheduler = BackgroundScheduler(timezone=str(TIMEZONE))
scheduler.start()

# Pool de threads para procesamiento paralelo de audio
audio_executor = ThreadPoolExecutor(max_workers=4)

# Colas de audio por número de teléfono para streaming
audio_queues = {}

# Lock para sincronizar acceso a las colas
audio_queues_lock = threading.Lock()

# Directorio para almacenar estado de conversaciones
conversations_dir = "conversations"
os.makedirs(conversations_dir, exist_ok=True)

# Directorio para transcripciones de llamadas
transcripts_dir = "transcripts"
os.makedirs(transcripts_dir, exist_ok=True)

# Directorio para análisis de IA
analysis_dir = "analysis"
os.makedirs(analysis_dir, exist_ok=True)

# Crea el directorio de audios si no existe
audio_dir = "audio"
os.makedirs(audio_dir, exist_ok=True)
app.mount("/audio", StaticFiles(directory=audio_dir), name="audio")

# Obtén la URL base pública desde el entorno
PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL', '')

# --- Funciones auxiliares para manejo de conversaciones ---
def get_conversation_file(number: str) -> str:
    """Obtiene la ruta del archivo de conversación para un número"""
    return os.path.join(conversations_dir, f"conversation-{number}.json")

def get_transcript_file(number: str) -> str:
    """Obtiene la ruta del archivo de transcripción para un número"""
    return os.path.join(transcripts_dir, f"transcript-{number}.json")

def get_analysis_file(number: str) -> str:
    """Obtiene la ruta del archivo de análisis para un número"""
    return os.path.join(analysis_dir, f"analysis-{number}.json")

def load_conversation_state(number: str) -> Dict[str, Any]:
    """Carga el estado de la conversación de un usuario"""
    file_path = get_conversation_file(number)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando conversación para {number}: {e}")
    
    # Estado inicial por defecto
    return {
        "stage": "initial",  # initial, call_in_progress, call_completed, analyzed, ready_for_human
        "name": "",
        "call_scheduled": False,
        "call_started": False,
        "call_completed": False,
        "call_duration": 0,
        "transcript_ready": False,
        "analysis_ready": False,
        "call_status": "pending",  # pending, in_progress, completed, failed
        "ai_analysis": {
            "interest_level": "unknown",  # high, medium, low, none
            "objections": [],
            "key_points": [],
            "next_action": "unknown",
            "human_followup_needed": False,
            "priority": "normal"  # high, normal, low
        },
        "last_interaction": datetime.now(TIMEZONE).isoformat(),
        "messages_sent": 0
    }

def save_conversation_state(number: str, state: Dict[str, Any]):
    """Guarda el estado de la conversación de un usuario"""
    file_path = get_conversation_file(number)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, default=str)
    except Exception as e:
        print(f"Error guardando conversación para {number}: {e}")

def save_transcript(number: str, transcript_data: Dict[str, Any]):
    """Guarda la transcripción de una llamada"""
    file_path = get_transcript_file(number)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, default=str)
        print(f"Transcripción guardada para {number}")
    except Exception as e:
        print(f"Error guardando transcripción para {number}: {e}")

def save_analysis(number: str, analysis_data: Dict[str, Any]):
    """Guarda el análisis de IA de una llamada"""
    file_path = get_analysis_file(number)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        print(f"Análisis guardado para {number}")
    except Exception as e:
        print(f"Error guardando análisis para {number}: {e}")

def get_current_time() -> datetime:
    """Obtiene la hora actual en Barranquilla"""
    return datetime.now(TIMEZONE)

def analyze_call_with_ai(transcript_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analiza la transcripción de la llamada usando IA para determinar el estado"""
    try:
        # Crear prompt para análisis
        transcript_text = ""
        for entry in transcript_data.get("conversation", []):
            role = entry.get("role", "")
            content = entry.get("content", "")
            timestamp = entry.get("timestamp", "")
            transcript_text += f"[{timestamp}] {role}: {content}\n"
        
        analysis_prompt = f"""
Analiza la siguiente transcripción de una llamada de ventas de préstamos por libranza y proporciona un análisis estructurado.

TRANSCRIPCIÓN:
{transcript_text}

Por favor analiza y responde en formato JSON con los siguientes campos:

{{
    "interest_level": "high|medium|low|none",
    "objections": ["lista de objeciones mencionadas"],
    "key_points": ["puntos clave de la conversación"],
    "next_action": "schedule_meeting|send_info|follow_up_call|close_deal|no_interest",
    "human_followup_needed": true/false,
    "priority": "high|normal|low",
    "summary": "resumen de 2-3 líneas de la conversación",
    "recommendations": ["recomendaciones para el seguimiento humano"]
}}

Criterios de análisis:
- interest_level: "high" si mostró mucho interés, "medium" si algo de interés, "low" si poco interés, "none" si no mostró interés
- objections: lista de objeciones o preocupaciones mencionadas
- key_points: información importante mencionada (situación financiera, necesidades, etc.)
- next_action: acción recomendada basada en el interés mostrado
- human_followup_needed: true si necesita seguimiento humano inmediato
- priority: "high" si es muy interesado, "normal" si es moderado, "low" si no mostró interés
"""

        # Llamar a Ollama para análisis
        response = ollama.chat(
            model='ana',
            messages=[
                {
                    'role': 'system',
                    'content': 'Eres un analista experto en ventas que analiza transcripciones de llamadas para determinar el nivel de interés y las acciones de seguimiento necesarias.'
                },
                {
                    'role': 'user',
                    'content': analysis_prompt
                }
            ]
        )
        
        # Intentar parsear la respuesta JSON
        ai_response = response['message']['content']
        
        # Buscar JSON en la respuesta
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            analysis = json.loads(json_match.group())
        else:
            # Fallback si no se puede parsear JSON
            analysis = {
                "interest_level": "unknown",
                "objections": [],
                "key_points": [],
                "next_action": "unknown",
                "human_followup_needed": False,
                "priority": "normal",
                "summary": "Análisis no disponible",
                "recommendations": ["Revisar transcripción manualmente"]
            }
        
        return analysis
        
    except Exception as e:
        print(f"Error analizando llamada con IA: {e}")
        return {
            "interest_level": "unknown",
            "objections": [],
            "key_points": [],
            "next_action": "unknown",
            "human_followup_needed": False,
            "priority": "normal",
            "summary": f"Error en análisis: {str(e)}",
            "recommendations": ["Revisar transcripción manualmente"]
        }

def schedule_call(number: str, name: str):
    """Programa una llamada inmediata para un contacto y genera el saludo personalizado"""
    try:
        print(f"Programando llamada inmediata para {number} ({name})")
        
        # Generar saludo personalizado ANTES de la llamada en paralelo
        greeting_text = (
            f"¡Alo {name}! ¿Cómo estás? Soy Ana de AVANZA. "
            f"Te llamo para ayudarte con tus finanzas. ¿Tienes 5 minutos? "
            f"Tenemos préstamos desde 1.6% mensual por libranza."
        )
        greeting_filename = f"audio/greeting_{number.replace('+', '').replace('-', '')}_{uuid.uuid4()}.wav"
        
        # Crear directorio de audio si no existe
        os.makedirs("audio", exist_ok=True)
        
        # Crear estado inicial con información del saludo
        state = load_conversation_state(number)
        state["stage"] = "call_in_progress"
        state["name"] = name
        state["greeting_audio_file"] = greeting_filename
        state["greeting_ready"] = False  # Flag para indicar si está listo
        state["greeting_generation_started"] = True
        save_conversation_state(number, state)
        
        # Generar saludo en thread separado para no bloquear
        def generate_greeting():
            try:
                print(f"🎤 Generando saludo personalizado para {name}...")
                if generate_speech_elevenlabs(greeting_text, greeting_filename):
                    greeting_url = f"{PUBLIC_BASE_URL}/audio/{os.path.basename(greeting_filename)}"
                    print(f"✅ Saludo generado: {greeting_url}")
                    
                    # Actualizar estado cuando esté listo
                    state = load_conversation_state(number)
                    state["greeting_audio_url"] = greeting_url
                    state["greeting_ready"] = True
                    save_conversation_state(number, state)
                    
                    return greeting_url
                else:
                    print("⚠️ Error generando saludo, se usará fallback")
                    # Marcar como fallback
                    state = load_conversation_state(number)
                    state["greeting_ready"] = True
                    state["greeting_fallback"] = True
                    save_conversation_state(number, state)
                    return None
            except Exception as e:
                print(f"❌ Error en generación de saludo: {e}")
                # Marcar como fallback
                state = load_conversation_state(number)
                state["greeting_ready"] = True
                state["greeting_fallback"] = True
                save_conversation_state(number, state)
                return None
        
        # Ejecutar generación de saludo en paralelo
        greeting_future = audio_executor.submit(generate_greeting)
        
        # Iniciar la llamada inmediatamente (no esperar el saludo)
        call = client.calls.create(
            to=number,
            from_=TWILIO_PHONE_NUMBER,
            url=TWILIO_WEBHOOK_URL
        )
        print(f"📞 Llamada iniciada: {call.sid}")
        
        # Actualizar estado con información de la llamada
        state = load_conversation_state(number)
        state["call_sid"] = call.sid
        state["call_started"] = True
        state["call_status"] = "in_progress"
        save_conversation_state(number, state)
        
        return call.sid
        
    except Exception as e:
        print(f"Error programando llamada para {number}: {e}")
        return None

def create_whatsapp_form_message(stage: str, name: str = "") -> str:
    """Crea mensajes estructurados con formularios para WhatsApp"""
    
    if stage == "initial":
        return f"""🎧 ¡Hola {name}! Soy ANA de AVANZA 💼

No te estoy escribiendo para venderte un crédito —te lo prometo—, sino para ayudarte a organizar tus finanzas, que es algo que todos necesitamos hoy en día.

📌 Tenemos tasas desde solo **1.6% mensual** por libranza
📌 Montos hasta $150 millones sin codeudor
📌 Sin importar si estás reportado en centrales
📌 Descuento directo de nómina

¿Puedo llamarte para explicártelo? No es una llamada comercial, es una charla entre tú y yo buscando la mejor forma de que el dinero te rinda más sin estrés.

¿Qué prefieres? 💰💪"""

    elif stage == "waiting_confirmation":
        return f"""🎯 ¡Perfecto {name}! 

Para agendar tu llamada y revisar tu elegibilidad para el préstamo AVANZA, dime cuándo te parece mejor:

⏰ Opciones:
• "Ahora mismo" - Te llamo en 10 minutos
• "En 2 horas" - Te llamo en 2 horas  
• "A las 3:30 PM" - Te llamo a esa hora
• "Mañana a las 10:00" - Te llamo mañana

¿Cuándo te viene mejor para revisar tu situación y calcular tu préstamo? 💰"""

    elif stage == "scheduled_call":
        return f"""✅ ¡Excelente {name}! 

Tu llamada está programada. Te llamaré puntualmente para revisar tu elegibilidad y explicarte todos los beneficios del préstamo AVANZA.

📋 En la llamada de 10 minutos revisaremos:
• Tu situación actual y capacidad de pago
• Cómo podemos bajarte esa cuota que te tiene apretado
• Monto que puedes obtener (hasta $150 millones)
• Documentación necesaria (solo cédula vigente)
• Proceso de desembolso (24-48 horas)

Si necesitas cambiar la hora, solo dime "cambiar hora" y te ayudo a reprogramarla.

¡Prepárate para mejorar tu salud financiera! 💰💪"""

    return "Gracias por tu tiempo. ¡Que tengas un excelente día!"

# --- Funciones para WhatsApp Business API ---
def send_whatsapp_business_message(to_number: str, message: str, name: str = "") -> Dict[str, Any]:
    """Envía mensaje usando WhatsApp Business API"""
    try:
        # Intentar con WhatsApp Business API primero
        result = whatsapp_business.send_text_message(to_number, message)
        
        if result.get("status") == "success":
            print(f"📱 Mensaje WhatsApp Business enviado: {result.get('message_id')}")
            return result
        else:
            print(f"⚠️ Error WhatsApp Business: {result.get('error')}")
            # Fallback a Twilio si está configurado
            if TWILIO_WHATSAPP_NUMBER:
                return send_whatsapp_message(to_number, message, name)
            else:
                return {"error": "WhatsApp no configurado"}
                
    except Exception as e:
        print(f"Error enviando mensaje WhatsApp Business: {e}")
        return {"error": str(e)}

# --- Funciones para manejo de documentos ---
def verify_document_names(cedula_name: str, recibo_name: str) -> bool:
    """Verifica que los nombres en cédula y recibo coincidan"""
    try:
        # Limpiar nombres (quitar espacios extra, normalizar)
        cedula_clean = cedula_name.strip().lower()
        recibo_clean = recibo_name.strip().lower()
        
        # Comparar nombres
        return cedula_clean == recibo_clean
    except Exception as e:
        print(f"Error verificando nombres: {e}")
        return False

def send_documents_email(to_email: str, cedula_file: str, recibo_file: str, customer_name: str):
    """Envía documentos por correo electrónico"""
    try:
        # Aquí implementarías el envío de correo
        # Por ahora solo simulamos
        print(f"\U0001F4E7 Enviando documentos por email a {to_email}")
        print(f"   Cliente: {customer_name}")
        print(f"   Cédula: {cedula_file}")
        print(f"   Recibo: {recibo_file}")
        
        return {
            "status": "success",
            "message": "Documentos enviados por correo",
            "email": to_email
        }
    except Exception as e:
        print(f"Error enviando email: {e}")
        return {"error": str(e)}

def create_whatsapp_form_message(stage: str, name: str = "") -> str:

def process_whatsapp_business_message(user_message: str, user_number: str, user_name: str = "") -> str:
    """Procesa mensaje de WhatsApp Business y retorna respuesta"""
    try:
        # Cargar estado de conversación
        state = load_conversation_state(user_number)
        current_stage = state.get("stage", "initial")
        
        # Actualizar última interacción
        state["last_interaction"] = get_current_time().isoformat()
        state["messages_sent"] = state.get("messages_sent", 0) + 1
        
        # Procesar según el estado actual
        if current_stage == "initial":
            # Primer mensaje - enviar presentación inicial
            response = f"""🎧 ¡Hola {user_name}! Soy ANA de AVANZA 💼

No te estoy escribiendo para venderte un crédito —te lo prometo—, sino para ayudarte a organizar tus finanzas, que es algo que todos necesitamos hoy en día.

📌 Tenemos tasas desde solo **1.6% mensual** por libranza
📌 Montos hasta $150 millones sin codeudor
📌 Sin importar si estás reportado en centrales
📌 Descuento directo de nómina

¿Puedo llamarte para explicártelo? No es una llamada comercial, es una charla entre tú y yo buscando la mejor forma de que el dinero te rinda más sin estrés.

¿Qué prefieres? 💰💪"""
            state["stage"] = "waiting_confirmation"
            
        elif current_stage == "waiting_confirmation":
            # Procesar respuesta del usuario
            user_message_lower = user_message.lower()
            
            if any(word in user_message_lower for word in ["sí", "si", "yes", "ok", "vale", "claro", "perfecto", "me interesa"]):
                # Usuario acepta llamada
                response = f"""✅ ¡Excelente {user_name}! 

Tu llamada está programada. Te llamaré puntualmente para revisar tu elegibilidad y explicarte todos los beneficios del préstamo AVANZA.

📋 En la llamada de 10 minutos revisaremos:
• Tu situación actual y capacidad de pago
• Cómo podemos bajarte esa cuota que te tiene apretado
• Monto que puedes obtener (hasta $150 millones)
• Documentación necesaria (solo cédula vigente)
• Proceso de desembolso (24-48 horas)

📞 Llamada programada. Te llamaré en 1 minuto."""
                state["stage"] = "scheduled_call"
                
                # Programar llamada inmediata
                call_sid = schedule_call(user_number, user_name)
                if not call_sid:
                    response += f"\n\n⚠️ Error programando llamada. Te contactaré pronto."
                    
            elif any(word in user_message_lower for word in ["no", "ahora no", "después", "más tarde", "no me interesa"]):
                # Usuario no quiere llamada - CONVENCER CON IA
                response = f"""Entiendo tu preocupación {user_name}, pero déjame explicarte algo importante:

¿Sabías que con nuestros préstamos puedes:
• Reducir tus cuotas mensuales hasta en un 40%
• Recibir hasta $150 millones sin codeudor
• Tener descuento directo por nómina (sin olvidos)
• Aprobación en 24-48 horas

Muchos de nuestros clientes han logrado ahorrar más de $500,000 mensuales. ¿Te parece que vale la pena que te explique cómo? Solo necesito 5 minutos de tu tiempo.

¿Me das esa oportunidad? 💰"""
                state["stage"] = "convincing"
                
            else:
                # Respuesta no clara - seguir convenciendo
                response = f"""No estoy segura de entender {user_name}. 

Te explico rápido: con AVANZA puedes:
✅ Recibir hasta $150 millones
✅ Pagar menos cada mes
✅ Sin codeudor ni reportes
✅ Descuento automático por nómina

¿Te parece interesante? Solo dime 'sí' y te explico todo en detalle. 💰"""
                
        elif current_stage == "convincing":
            # Usuario no quería llamada - seguir convenciendo
            user_message_lower = user_message.lower()
            
            if any(word in user_message_lower for word in ["sí", "si", "yes", "ok", "vale", "claro", "perfecto", "me interesa", "explicame"]):
                # Cambió de opinión
                response = f"""🎯 ¡Perfecto {user_name}! 

Para agendar tu llamada y revisar tu elegibilidad para el préstamo AVANZA, dime cuándo te parece mejor:

⏰ Opciones:
• "Ahora mismo" - Te llamo en 10 minutos
• "En 2 horas" - Te llamo en 2 horas  
• "A las 3:30 PM" - Te llamo a esa hora
• "Mañana a las 10:00" - Te llamo mañana

¿Cuándo te viene mejor para revisar tu situación y calcular tu préstamo? 💰"""
                state["stage"] = "scheduled_call"
                
                # Programar llamada inmediata
                call_sid = schedule_call(user_number, user_name)
                if call_sid:
                    response += f"\n\n📞 Llamada programada. Te llamaré en 1 minuto."
                else:
                    response += f"\n\n⚠️ Error programando llamada. Te contactaré pronto."
            else:
                # Seguir convenciendo
                response = f"""Entiendo {user_name}, pero déjame contarte algo:

María, una docente como tú, logró reducir su cuota de $800,000 a $450,000 mensuales. Eso significa $350,000 más en su bolsillo cada mes.

¿Te imaginas qué podrías hacer con ese dinero extra? Pagar deudas, ahorrar, o simplemente vivir más tranquila.

¿Vale la pena que te explique cómo? Solo 5 minutos. 💰"""
                
        elif current_stage == "scheduled_call":
            # Llamada ya programada
            response = "Tu llamada ya está programada. Te llamaré puntualmente. Si necesitas cambiar la hora, solo dime 'cambiar hora'."
            
        elif current_stage == "call_completed":
            # Llamada terminada - verificar interés
            user_message_lower = user_message.lower()
            
            if any(word in user_message_lower for word in ["sí", "si", "yes", "ok", "vale", "claro", "perfecto", "me interesa", "quiero", "proceder"]):
                # Usuario interesado después de la llamada
                response = f"""🎉 ¡Excelente {user_name}! 

Perfecto, para continuar con tu solicitud necesito que me envíes estos documentos:

📋 Documentos requeridos:
1. 📄 Cédula de ciudadanía (frente y reverso)
2. 💰 Último recibo de pago de nómina
3. 📝 Formato de autorización (te lo envío ahora)

📱 Envíalos por WhatsApp a este mismo número
📧 O por email a: info@avanza.lat

¿Tienes estos documentos a la mano? 📄"""
                state["stage"] = "waiting_documents"
                
            else:
                # Usuario no interesado después de la llamada
                response = f"""Entiendo {user_name}. 

Si en el futuro necesitas ayuda financiera, recuerda que estamos aquí para ayudarte. 

¿Te parece bien que te mantenga informado sobre nuestras promociones especiales? 💰"""
                state["stage"] = "not_interested"
                
        elif current_stage == "waiting_documents":
            # Esperando documentos
            response = f"""Perfecto {user_name}. 

Por favor envía:
1. 📄 Cédula de ciudadanía (frente y reverso)
2. 💰 Último recibo de pago de nómina
3. 📝 Formato de autorización

Una vez que los reciba, los revisaré y te confirmaré el siguiente paso.

¿Ya los tienes listos? 📄"""
            state["stage"] = "documents_received"
            
        elif current_stage == "documents_received":
            # Documentos recibidos - verificar nombres
            # Aquí se procesarían los documentos
            response = f"""✅ ¡Perfecto {user_name}! 

He recibido tus documentos. Los estoy revisando ahora mismo.

📋 Próximos pasos:
1. ✅ Revisión de documentos
2. 📊 Evaluación financiera
3. 📞 Confirmación de aprobación
4. 💰 Desembolso en 24-48 horas

Te mantendré informado del proceso. ¡Gracias por confiar en AVANZA! 🎉"""
            state["stage"] = "documents_verified"
            
        else:
            # Estado desconocido
            response = "Gracias por tu interés. Te contactaré pronto."
            state["stage"] = "initial"
        
        # Guardar estado actualizado
        save_conversation_state(user_number, state)
        
        return response
        
    except Exception as e:
        print(f"Error procesando mensaje WhatsApp Business: {e}")
        return "Lo siento, hubo un error procesando tu mensaje. Te contactaré pronto."

def generate_speech_elevenlabs(text, output_file):
    """Genera audio usando ElevenLabs optimizado para velocidad"""
    try:
        if not elevenlabs_client:
            print("Error: ElevenLabs client no configurado")
            return False
        
        # Optimizar texto para velocidad (reducir pausas innecesarias)
        optimized_text = text.replace("  ", " ").strip()
        
        # Generar audio con ElevenLabs usando configuración optimizada
        audio = elevenlabs_client.text_to_speech.convert(
            text=optimized_text,
            voice_id=ELEVENLABS_VOICE_ID,
            model_id="eleven_multilingual_v2",
            voice_settings={
                "stability": 0.5,  # Menor estabilidad = más rápido
                "similarity_boost": 0.75,  # Balance entre velocidad y calidad
                "style": 0.0,  # Sin estilo adicional para mayor velocidad
                "use_speaker_boost": True
            }
        )
        
        # Guardar audio temporal (puede ser MP3 o WAV)
        temp_file = output_file + ".temp"
        with open(temp_file, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        
        try:
            # Intentar detectar el formato automáticamente
            audio_segment = AudioSegment.from_file(temp_file)
            
            # Optimizar para Twilio: 8kHz mono
            audio_segment = audio_segment.set_frame_rate(8000).set_channels(1)
            
            # Aplicar normalización para mejor calidad
            audio_segment = audio_segment.normalize()
            
            # Exportar como WAV optimizado
            audio_segment.export(output_file, format="wav")
            
        except Exception as e:
            print(f"Error procesando audio: {e}")
            # Fallback: intentar con ffmpeg directamente
            try:
                import subprocess
                subprocess.run([
                    'ffmpeg', '-i', temp_file, 
                    '-ar', '8000', '-ac', '1', 
                    '-acodec', 'pcm_s16le', 
                    output_file
                ], check=True, capture_output=True)
                print(f"✅ Audio convertido con ffmpeg: {output_file}")
            except Exception as ffmpeg_error:
                print(f"Error con ffmpeg: {ffmpeg_error}")
                # Último fallback: copiar archivo temporal
                import shutil
                shutil.copy2(temp_file, output_file)
        
        # Limpiar archivo temporal
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        return True
        
    except Exception as e:
        print(f"Error generando audio con ElevenLabs: {e}")
        # Limpiar archivo temporal si existe
        temp_file = output_file + ".temp"
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False

def get_audio_queue(number: str) -> queue.Queue:
    """Obtiene o crea la cola de audio para un número específico"""
    with audio_queues_lock:
        if number not in audio_queues:
            audio_queues[number] = queue.Queue()
        return audio_queues[number]

def cleanup_audio_queue(number: str):
    """Limpia la cola de audio para un número específico"""
    with audio_queues_lock:
        if number in audio_queues:
            del audio_queues[number]

def cleanup_old_audio_files():
    """Limpia archivos de audio antiguos para liberar espacio"""
    try:
        audio_dir = "audio"
        if not os.path.exists(audio_dir):
            return
        
        current_time = time.time()
        max_age = 3600  # 1 hora
        
        for filename in os.listdir(audio_dir):
            if filename.endswith('.wav'):
                file_path = os.path.join(audio_dir, filename)
                file_age = current_time - os.path.getmtime(file_path)
                
                if file_age > max_age:
                    try:
                        os.remove(file_path)
                        print(f"🗑️ Limpiado archivo antiguo: {filename}")
                    except Exception as e:
                        print(f"Error eliminando {filename}: {e}")
        
    except Exception as e:
        print(f"Error en limpieza de audio: {e}")

def generate_audio_chunk(text_chunk: str, number: str) -> str:
    """Genera audio para un chunk de texto y retorna el nombre del archivo"""
    if not text_chunk.strip():
        return None
    
    audio_filename = f"audio/chunk_{number.replace('+', '').replace('-', '')}_{uuid.uuid4()}.wav"
    
    if generate_speech_elevenlabs(text_chunk.strip(), audio_filename):
        return audio_filename
    
    # Fallback: crear archivo de audio simple
    try:
        import wave
        import struct
        
        # Crear un archivo WAV simple con silencio
        with wave.open(audio_filename, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(8000)  # 8kHz
            
            # Generar 1 segundo de silencio
            silence = struct.pack('<h', 0) * 8000
            wav_file.writeframes(silence)
        
        print(f"⚠️ Usando fallback de audio para: {text_chunk[:30]}...")
        return audio_filename
    except Exception as e:
        print(f"Error creando fallback de audio: {e}")
        return None

def process_ai_response_sync(history: List[Dict], number: str, transcript_data: Dict):
    """Procesa la respuesta de IA de forma secuencial: primero texto, luego audio"""
    try:
        # Obtener respuesta completa de Ollama (sin streaming)
        response = ollama.chat(
            model='ana',
            messages=history
        )
        
        # Extraer el texto completo de la respuesta
        ai_response = response['message']['content']
        print(f"📝 Respuesta de IA obtenida: {len(ai_response)} caracteres")
        
        # Actualizar transcripción con la respuesta completa
        transcript_data["conversation"].append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": get_current_time().isoformat()
        })
        save_transcript(number, transcript_data)
        
        # Generar audio completo para toda la respuesta
        print(f"🎤 Generando audio para respuesta completa...")
        audio_filename = f"audio/response_{number.replace('+', '').replace('-', '')}_{uuid.uuid4()}.wav"
        
        if generate_speech_elevenlabs(ai_response, audio_filename):
            print(f"✅ Audio generado exitosamente: {audio_filename}")
            return ai_response, [audio_filename]
        else:
            print("⚠️ Error generando audio, usando fallback")
            return ai_response, []
        
    except Exception as e:
        print(f"Error procesando respuesta de IA: {e}")
        return "Lo siento, hubo un error procesando tu mensaje.", []

# --- Endpoints principales ---
@app.get("/")
def read_root():
    return {"message": "Sistema ANA - Llamadas automáticas con análisis de IA"}

@app.get("/test-tts")
def test_tts():
    """Endpoint de prueba para TTS"""
    test_text = "Hola, soy Ana tu asesora financiera de AVANZA. ¿Cómo estás?"
    test_filename = f"audio/test_{uuid.uuid4()}.wav"
    
    if generate_speech_elevenlabs(test_text, test_filename):
        return {
            "status": "success",
            "message": "Audio generado exitosamente",
            "file": test_filename,
            "url": f"{PUBLIC_BASE_URL}/audio/{os.path.basename(test_filename)}"
        }
    else:
        return {"status": "error", "message": "Error generando audio"}

@app.post("/cleanup-audio")
def cleanup_audio():
    """Limpia archivos de audio antiguos"""
    try:
        cleanup_old_audio_files()
        return {
            "status": "success",
            "message": "Limpieza de audio completada"
        }
    except Exception as e:
        return {"status": "error", "message": f"Error en limpieza: {str(e)}"}

@app.get("/audio-stats")
def get_audio_stats():
    """Obtiene estadísticas de archivos de audio"""
    try:
        audio_dir = "audio"
        if not os.path.exists(audio_dir):
            return {"total_files": 0, "total_size": "0 MB"}
        
        files = os.listdir(audio_dir)
        total_size = 0
        
        for filename in files:
            if filename.endswith('.wav'):
                file_path = os.path.join(audio_dir, filename)
                total_size += os.path.getsize(file_path)
        
        return {
            "total_files": len([f for f in files if f.endswith('.wav')]),
            "total_size": f"{total_size / (1024*1024):.1f} MB",
            "active_queues": len(audio_queues)
        }
    except Exception as e:
        return {"error": f"Error obteniendo estadísticas: {str(e)}"}

class CreateRepresentativeRequest(BaseModel):
    model_name: str
    from_model: str
    temperature: float
    num_ctx: int
    system_prompt: str

@app.post("/createRepresentative")
def create_representative(req: CreateRepresentativeRequest):
    """Crea un nuevo modelo representante usando Ollama"""
    try:
        # Leer el prompt del sistema desde archivo
        system_prompt_path = "system_prompt_updated.txt"
        if os.path.exists(system_prompt_path):
            with open(system_prompt_path, 'r', encoding='utf-8') as f:
                system_prompt = f.read()
        else:
            system_prompt = req.system_prompt
        
        # Crear el modelo usando Ollama
        create_command = [
            "ollama", "create", req.model_name,
            "--from", req.from_model,
            "--modelfile", f"""
FROM {req.from_model}
PARAMETER temperature {req.temperature}
PARAMETER num_ctx {req.num_ctx}
SYSTEM {system_prompt}
"""
        ]
        
        result = subprocess.run(create_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            return {
                "status": "success",
                "message": f"Modelo {req.model_name} creado exitosamente",
                "details": result.stdout
            }
        else:
            return {
                "status": "error",
                "message": f"Error creando modelo: {result.stderr}",
                "details": result.stdout
            }
            
    except Exception as e:
        return {"status": "error", "message": f"Error: {str(e)}"}

class ScheduleCallRequest(BaseModel):
    number: str
    name: str

@app.post("/schedule_call")
def schedule_call_endpoint(request: ScheduleCallRequest):
    """Endpoint para programar una llamada inmediata"""
    try:
        call_sid = schedule_call(request.number, request.name)
        if call_sid:
            return {
                "status": "success",
                "message": f"Llamada programada para {request.name}",
                "call_sid": call_sid
            }
        else:
            return {
                "status": "error",
                "message": "Error programando la llamada"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {str(e)}"
        }

@app.get("/conversations/status")
def get_conversations_status():
    """Obtiene el estado de todas las conversaciones"""
    try:
        conversations = []
        current_time = get_current_time()
        
        if os.path.exists(conversations_dir):
            for filename in os.listdir(conversations_dir):
                if filename.startswith("conversation-") and filename.endswith(".json"):
                    number = filename.replace("conversation-", "").replace(".json", "")
                    
                    try:
                        with open(os.path.join(conversations_dir, filename), 'r', encoding='utf-8') as f:
                            state = json.load(f)
                        
                        # Calcular tiempo desde última interacción
                        last_interaction = datetime.fromisoformat(state.get("last_interaction", current_time.isoformat()))
                        time_diff = current_time - last_interaction.replace(tzinfo=TIMEZONE)
                        
                        conversations.append({
                            "number": number,
                            "name": state.get("name", ""),
                            "stage": state.get("stage", "unknown"),
                            "call_status": state.get("call_status", "unknown"),
                            "call_duration": state.get("call_duration", 0),
                            "transcript_ready": state.get("transcript_ready", False),
                            "analysis_ready": state.get("analysis_ready", False),
                            "ai_analysis": state.get("ai_analysis", {}),
                            "messages_sent": state.get("messages_sent", 0),
                            "last_interaction": state.get("last_interaction", ""),
                            "time_since_last_interaction": str(time_diff).split('.')[0]
                        })
                    except Exception as e:
                        print(f"Error procesando conversación {filename}: {e}")
                        continue
        
        return {
            "total_conversations": len(conversations),
            "current_time": current_time.isoformat(),
            "timezone": str(TIMEZONE),
            "conversations": conversations
        }
        
    except Exception as e:
        return {"error": f"Error obteniendo estado: {str(e)}"}

@app.post("/twilio/voice")
async def twilio_voice(request: Request):
    """Maneja llamadas entrantes de Twilio"""
    response = VoiceResponse()
    
    # Obtener el número del usuario
    form = await request.form()
    from_number = form.get('From', '')
    call_sid = form.get('CallSid', '')
    
    if from_number.startswith('whatsapp:'):
        user_number = from_number.replace('whatsapp:', '').strip()
    else:
        user_number = from_number.strip()
    
    if not user_number.startswith('+'):
        user_number = '+' + user_number
    
    # Cargar estado de conversación para obtener el nombre
    state = load_conversation_state(user_number)
    user_name = state.get("name", "mi cielo")
    
    # Inicializar transcripción si no existe
    if not state.get("transcript_ready", False):
        transcript_data = {
            "call_sid": call_sid,
            "number": user_number,
            "name": user_name,
            "start_time": get_current_time().isoformat(),
            "conversation": []
        }
        save_transcript(user_number, transcript_data)
        state["transcript_ready"] = True
        save_conversation_state(user_number, state)
    
    # Verificar si hay saludo pre-generado y esperar si es necesario
    greeting_audio_url = state.get("greeting_audio_url")
    greeting_audio_file = state.get("greeting_audio_file")
    greeting_ready = state.get("greeting_ready", False)
    greeting_fallback = state.get("greeting_fallback", False)
    
    # Si la generación empezó pero no está lista, esperar un poco
    if state.get("greeting_generation_started") and not greeting_ready and not greeting_fallback:
        print(f"⏳ Esperando que se complete la generación del saludo para {user_name}...")
        max_wait = 5  # Máximo 5 segundos de espera
        wait_time = 0
        while wait_time < max_wait and not greeting_ready and not greeting_fallback:
            time.sleep(0.5)
            wait_time += 0.5
            # Recargar estado para ver si cambió
            state = load_conversation_state(user_number)
            greeting_ready = state.get("greeting_ready", False)
            greeting_fallback = state.get("greeting_fallback", False)
            greeting_audio_url = state.get("greeting_audio_url")
            greeting_audio_file = state.get("greeting_audio_file")
    
    # Usar saludo pre-generado si está disponible y el archivo existe
    if greeting_ready and greeting_audio_url and greeting_audio_file and os.path.exists(greeting_audio_file):
        print(f"🎤 Usando saludo pre-generado: {greeting_audio_url}")
        response.play(greeting_audio_url)
        greeting_text = (
            f"Hola {user_name}! ¿Cómo estás? Soy Ana de AVANZA. "
            f"Te llamo para ayudarte con tus finanzas. ¿Tienes 5 minutos? "
            f"Tenemos préstamos desde 1.6% mensual por libranza."
        )
    else:
        print("⚠️ No se encontró saludo pre-generado o hubo error, generando uno nuevo...")
        # Generar saludo personalizado con ElevenLabs siguiendo el guion de 10 minutos
        greeting_text = (
            f"Hola {user_name}! ¿Cómo estás? Soy Ana de AVANZA. "
            f"Te llamo para ayudarte con tus finanzas. ¿Tienes 5 minutos? "
            f"Tenemos préstamos desde 1.6% mensual por libranza."
        )
        greeting_filename = f"audio/greeting_{uuid.uuid4()}.wav"
        
        if generate_speech_elevenlabs(greeting_text, greeting_filename):
            greeting_url = f"{PUBLIC_BASE_URL}/audio/{os.path.basename(greeting_filename)}"
            print(f"Saludo generado exitosamente: {greeting_url}")
            response.play(greeting_url)
        else:
            print("Error generando saludo, usando fallback")
            response.say(
                f"¡Alo {user_name}! ¿Cómo estás? Soy Ana de AVANZA. "
                "Te llamo para ayudarte con tus finanzas. ¿Tienes 5 minutos? "
                "Tenemos préstamos desde 1.6% mensual por libranza.",
                language="es-ES"
            )
    
    # Guardar saludo en transcripción
    transcript_data = {
        "call_sid": call_sid,
        "number": user_number,
        "name": user_name,
        "start_time": get_current_time().isoformat(),
        "conversation": [
            {
                "role": "assistant",
                "content": greeting_text,
                "timestamp": get_current_time().isoformat()
            }
        ]
    }
    save_transcript(user_number, transcript_data)
    
    response.gather(
        input="speech",
        language="es-ES",
        action="/twilio/voice/handle_speech",
        method="POST",
        timeout=7,
        speechTimeout="auto"
    )
    
    # Generar despedida personalizada con ElevenLabs
    goodbye_text = "No se detectó audio. Ha sido un placer hablar contigo. ¡Que tengas un excelente día!"
    goodbye_filename = f"audio/goodbye_{uuid.uuid4()}.wav"
    
    if generate_speech_elevenlabs(goodbye_text, goodbye_filename):
        goodbye_url = f"{PUBLIC_BASE_URL}/audio/{os.path.basename(goodbye_filename)}"
        response.play(goodbye_url)
    else:
        response.say("No se detectó audio. Adiós.", language="es-ES")
    
    response.hangup()
    return PlainTextResponse(str(response), media_type="application/xml")

@app.post("/twilio/voice/handle_speech")
async def handle_speech(request: Request):
    """Maneja el reconocimiento de voz durante las llamadas"""
    form = await request.form()
    speech_result = form.get('SpeechResult', '').strip()
    from_number = form.get('From', '')
    call_sid = form.get('CallSid', '')
    
    print(f"SpeechResult: {speech_result}")
    print(f"From: {from_number}")
    
    user_number = from_number.replace('whatsapp:', '').strip()
    if not user_number.startswith('+'):
        user_number = '+' + user_number
    
    # Cargar transcripción actual
    transcript_file = get_transcript_file(user_number)
    if os.path.exists(transcript_file):
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
    else:
        transcript_data = {
            "call_sid": call_sid,
            "number": user_number,
            "name": "",
            "start_time": get_current_time().isoformat(),
            "conversation": []
        }
    
    # Agregar respuesta del usuario a la transcripción
    transcript_data["conversation"].append({
        "role": "user",
        "content": speech_result,
        "timestamp": get_current_time().isoformat()
    })
    
    # Generar respuesta de IA con streaming
    try:
        # Crear historial de conversación para IA
        history = []
        for entry in transcript_data["conversation"]:
            history.append({
                'role': entry['role'],
                'content': entry['content']
            })
        
        # Procesar respuesta de IA de forma secuencial
        print(f"🔄 Procesando respuesta de IA para {user_number}...")
        
        # Ejecutar procesamiento en thread separado
        def run_ai_processing():
            return process_ai_response_sync(history, user_number, transcript_data)
        
        # Ejecutar en thread pool
        future = audio_executor.submit(run_ai_processing)
        
        # Esperar a que se complete todo el procesamiento
        print(f"⏳ Esperando a que se complete el procesamiento para {user_number}...")
        try:
            ai_reply, audio_files = future.result(timeout=45)  # Timeout de 45 segundos
            print(f"✅ Procesamiento completado: {len(audio_files)} archivos de audio")
            
            # Construir respuesta
            response = VoiceResponse()
            
            if audio_files:
                # Reproducir el archivo de audio completo
                audio_url = f"{PUBLIC_BASE_URL}/audio/{os.path.basename(audio_files[0])}"
                response.play(audio_url)
                print(f"🎤 Reproduciendo audio completo: {audio_files[0]}")
            else:
                # Usar fallback si no se generó audio
                print("⚠️ No se generó audio, usando fallback")
                response.say("Lo siento, hubo un error generando la respuesta.", language="es-ES")
                
        except Exception as e:
            print(f"❌ Error en procesamiento: {e}")
            ai_reply = "Lo siento, hubo un error procesando tu mensaje."
            response = VoiceResponse()
            response.say("Lo siento, hubo un error generando la respuesta.", language="es-ES")
        
    except Exception as e:
        print(f"Error en streaming de IA: {e}")
        ai_reply = "Lo siento, hubo un error procesando tu mensaje."
        response = VoiceResponse()
        response.say("Lo siento, hubo un error generando la respuesta.", language="es-ES")
    
    # Gather después del play
    response.gather(
        input="speech",
        language="es-ES",
        action="/twilio/voice/handle_speech",
        method="POST",
        timeout=10,
        speechTimeout="auto"
    )
    
    # Generar despedida personalizada con ElevenLabs
    goodbye_text = "No se detectó audio. Ha sido un placer hablar contigo. ¡Que tengas un excelente día!"
    goodbye_filename = f"audio/goodbye_{uuid.uuid4()}.wav"
    
    if generate_speech_elevenlabs(goodbye_text, goodbye_filename):
        goodbye_url = f"{PUBLIC_BASE_URL}/audio/{os.path.basename(goodbye_filename)}"
        response.play(goodbye_url)
    else:
        response.say("No se detectó audio. Adiós.", language="es-ES")
    
    response.hangup()
    
    # Limpiar cola de audio para este número
    cleanup_audio_queue(user_number)
    
    return PlainTextResponse(str(response), media_type="application/xml")

@app.post("/twilio/voice/call_ended")
async def call_ended(request: Request):
    """Maneja el final de las llamadas y analiza la transcripción"""
    form = await request.form()
    call_sid = form.get('CallSid', '')
    from_number = form.get('From', '')
    call_duration = form.get('CallDuration', '0')
    
    user_number = from_number.replace('whatsapp:', '').strip()
    if not user_number.startswith('+'):
        user_number = '+' + user_number
    
    print(f"Llamada terminada para {user_number}, duración: {call_duration} segundos")
    
    # Actualizar estado de la conversación
    state = load_conversation_state(user_number)
    state["call_completed"] = True
    state["call_duration"] = int(call_duration)
    state["call_status"] = "completed"
    state["stage"] = "call_completed"
    save_conversation_state(user_number, state)
    
    # Cargar transcripción
    transcript_file = get_transcript_file(user_number)
    if os.path.exists(transcript_file):
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        
        # Agregar información de finalización
        transcript_data["end_time"] = get_current_time().isoformat()
        transcript_data["call_duration"] = int(call_duration)
        save_transcript(user_number, transcript_data)
        
        # Analizar transcripción con IA
        print(f"Analizando transcripción para {user_number}...")
        analysis = analyze_call_with_ai(transcript_data)
        
        # Guardar análisis
        save_analysis(user_number, analysis)
        
        # Actualizar estado con análisis
        state["analysis_ready"] = True
        state["ai_analysis"] = analysis
        state["stage"] = "call_completed"  # Cambiar a call_completed para continuar por WhatsApp
        
        # Determinar si necesita seguimiento humano
        if analysis.get("human_followup_needed", False) or analysis.get("interest_level") in ["high", "medium"]:
            state["stage"] = "ready_for_human"
        
        save_conversation_state(user_number, state)
        
        print(f"Análisis completado para {user_number}: {analysis.get('interest_level', 'unknown')} interés")
    
    # Limpiar cola de audio para este número
    cleanup_audio_queue(user_number)
    
    # Limpiar archivos de audio antiguos periódicamente
    if int(call_duration) % 300 == 0:  # Cada 5 minutos
        cleanup_old_audio_files()
    
    return PlainTextResponse("OK")

# --- Historial de chat por usuario (archivo) ---
def get_chatlog_path(number):
    return f"chatlog-{number}.txt"

def load_history(number):
    path = get_chatlog_path(number)
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    history = []
    for line in lines:
        if line.startswith('user:'):
            history.append({'role': 'user', 'content': line[len('user:'):].strip()})
        elif line.startswith('assistant:'):
            history.append({'role': 'assistant', 'content': line[len('assistant:'):].strip()})
    return history

def append_to_history(number, role, content):
    path = get_chatlog_path(number)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(f"{role}:{content}\n")

# --- Endpoint para procesar contactos y hacer llamadas directas ---
@app.post("/sendNumbers")
async def send_numbers(file: UploadFile = File(...)):
    """Procesa archivo Excel con contactos y hace llamadas directas + envía mensajes WhatsApp"""
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            return {"error": "El archivo debe ser un Excel (.xlsx o .xls)"}
        
        # Leer archivo Excel
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        
        # Validar columnas requeridas
        required_columns = ['numero']
        if not all(col in df.columns for col in required_columns):
            return {"error": f"El archivo debe contener las columnas: {required_columns}"}
        
        # Procesar contactos
        valid_contacts = []
        invalid_numbers = []
        results = []
        
        for index, row in df.iterrows():
            try:
                # Obtener número
                numero = str(row['numero']).strip()
                nombre = str(row.get('nombre', '')).strip() if 'nombre' in df.columns else ""
                
                # Limpiar número
                numero = re.sub(r'[^\d+]', '', numero)
                if not numero.startswith('+'):
                    numero = '+' + numero
                
                # Validar número (mínimo 10 dígitos)
                digits_only = re.sub(r'[^\d]', '', numero)
                if len(digits_only) < 10:
                    invalid_numbers.append({
                        "row": index + 1,
                        "numero": numero,
                        "nombre": nombre,
                        "error": "Número muy corto"
                    })
                    continue
                
                # 1. ENVIAR MENSAJE DE WHATSAPP PRIMERO
                whatsapp_message = create_whatsapp_form_message("initial", nombre)
                whatsapp_result = send_whatsapp_business_message(numero, whatsapp_message, nombre)
                
                # 2. PROGRAMAR LLAMADA TELEFÓNICA
                call_sid = schedule_call(numero, nombre)
                
                # Crear resultado combinado
                contact_result = {
                        "numero": numero,
                        "nombre": nombre,
                    "whatsapp_sent": whatsapp_result.get("status") == "success",
                    "whatsapp_message_id": whatsapp_result.get("message_id"),
                    "call_scheduled": call_sid is not None,
                        "call_sid": call_sid
                }
                
                if whatsapp_result.get("status") == "success" or call_sid:
                    valid_contacts.append(contact_result)
                    
                    # Determinar status principal
                    if whatsapp_result.get("status") == "success" and call_sid:
                        status = "whatsapp_y_llamada_programados"
                    elif whatsapp_result.get("status") == "success":
                        status = "whatsapp_enviado"
                    else:
                        status = "llamada_programada"
                    
                    results.append({
                        "numero": numero,
                        "nombre": nombre,
                        "status": status,
                        "whatsapp_message_id": whatsapp_result.get("message_id"),
                        "call_sid": call_sid
                    })
                else:
                    invalid_numbers.append({
                        "row": index + 1,
                        "numero": numero,
                        "nombre": nombre,
                        "error": "Error enviando WhatsApp y programando llamada"
                    })
                
                # Pausa entre contactos para evitar rate limits
                time.sleep(1)
                
            except Exception as e:
                invalid_numbers.append({
                    "row": index + 1,
                    "numero": str(row.get('numero', '')),
                    "nombre": str(row.get('nombre', '')),
                    "error": str(e)
                })
        
        return {
            "message": f"Procesamiento completado. {len(valid_contacts)} contactos procesados.",
            "total_contacts": len(df),
            "valid_contacts": len(valid_contacts),
            "invalid_contacts": len(invalid_numbers),
            "results": results,
            "invalid_numbers": invalid_numbers
        }
        
    except Exception as e:
        return {"error": f"Error procesando archivo: {str(e)}"}

# --- Endpoint para obtener análisis listos para seguimiento humano ---
@app.get("/analysis/ready_for_human")
def get_ready_for_human():
    """Obtiene todas las conversaciones listas para seguimiento humano"""
    try:
        ready_conversations = []
        
        if os.path.exists(conversations_dir):
            for filename in os.listdir(conversations_dir):
                if filename.startswith("conversation-") and filename.endswith(".json"):
                    number = filename.replace("conversation-", "").replace(".json", "")
                    
                    try:
                        with open(os.path.join(conversations_dir, filename), 'r', encoding='utf-8') as f:
                            state = json.load(f)
                        
                        if state.get("stage") == "ready_for_human":
                            # Cargar transcripción
                            transcript_file = get_transcript_file(number)
                            transcript_data = None
                            if os.path.exists(transcript_file):
                                with open(transcript_file, 'r', encoding='utf-8') as f:
                                    transcript_data = json.load(f)
                            
                            # Cargar análisis
                            analysis_file = get_analysis_file(number)
                            analysis_data = None
                            if os.path.exists(analysis_file):
                                with open(analysis_file, 'r', encoding='utf-8') as f:
                                    analysis_data = json.load(f)
                            
                            ready_conversations.append({
                                "number": number,
                                "name": state.get("name", ""),
                                "call_duration": state.get("call_duration", 0),
                                "ai_analysis": state.get("ai_analysis", {}),
                                "transcript": transcript_data,
                                "analysis": analysis_data,
                                "last_interaction": state.get("last_interaction", "")
                            })
                    except Exception as e:
                        print(f"Error procesando conversación {filename}: {e}")
                        continue
        
        return {
            "total_ready": len(ready_conversations),
            "conversations": ready_conversations
        }
        
    except Exception as e:
        return {"error": f"Error obteniendo conversaciones listas: {str(e)}"}

# --- Endpoint para marcar conversación como cerrada por humano ---
@app.post("/analysis/mark_closed")
def mark_conversation_closed(number: str, outcome: str, notes: str = ""):
    """Marca una conversación como cerrada por un humano"""
    try:
        state = load_conversation_state(number)
        state["stage"] = "closed_by_human"
        state["human_outcome"] = outcome
        state["human_notes"] = notes
        state["closed_at"] = get_current_time().isoformat()
        save_conversation_state(number, state)
        
        return {
            "status": "success",
            "message": f"Conversación {number} marcada como cerrada",
            "outcome": outcome
        }
        
    except Exception as e:
        return {"error": f"Error marcando conversación: {str(e)}"}

# --- Endpoints para WhatsApp Business API ---

@app.post("/send_whatsapp")
async def send_whatsapp_endpoint(request: Request):
    """Endpoint para enviar mensajes de WhatsApp manualmente"""
    try:
        form = await request.form()
        to_number = form.get('to', '')
        message = form.get('message', '')
        name = form.get('name', '')
        
        if not to_number or not message:
            return {"error": "Se requieren 'to' y 'message'"}
        
        # Limpiar número
        if not to_number.startswith('+'):
            to_number = '+' + to_number
        
        # Enviar mensaje usando WhatsApp Business API
        result = send_whatsapp_business_message(to_number, message, name)
        
        if result.get("status") == "success":
            return {
                "status": "success",
                "message": "Mensaje enviado exitosamente",
                "message_id": result.get("message_id"),
                "provider": "whatsapp_business"
            }
        else:
            return {
                "status": "error",
                "message": f"Error enviando mensaje: {result.get('error')}"
            }
            
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

@app.post("/whatsapp/business/send")
async def send_whatsapp_business_endpoint(request: Request):
    """Endpoint específico para WhatsApp Business API"""
    try:
        form = await request.form()
        to_number = form.get('to', '')
        message = form.get('message', '')
        template_name = form.get('template_name', '')
        language_code = form.get('language_code', 'es')
        
        if not to_number:
            return {"error": "Se requiere 'to'"}
        
        # Limpiar número
        if not to_number.startswith('+'):
            to_number = '+' + to_number
        
        # Enviar mensaje
        if template_name:
            # Enviar plantilla
            result = whatsapp_business.send_template_message(to_number, template_name, language_code)
        else:
            # Enviar mensaje de texto
            result = whatsapp_business.send_text_message(to_number, message)
        
        if result.get("status") == "success":
            return {
                "status": "success",
                "message": "Mensaje enviado exitosamente",
                "message_id": result.get("message_id"),
                "provider": "whatsapp_business"
            }
        else:
            return {
                "status": "error",
                "message": f"Error enviando mensaje: {result.get('error')}"
            }
            
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

@app.post("/whatsapp/business/webhook")
async def whatsapp_business_webhook(request: Request):
    """Webhook para recibir mensajes de WhatsApp Business API"""
    try:
        # Verificar si es verificación de webhook
        params = dict(request.query_params)
        if 'hub.mode' in params and 'hub.verify_token' in params:
            challenge = whatsapp_business.verify_webhook(
                params['hub.mode'],
                params['hub.verify_token'],
                params.get('hub.challenge', '')
            )
            if challenge:
                return PlainTextResponse(challenge)
            else:
                return PlainTextResponse("Forbidden", status_code=403)
        
        # Procesar mensaje entrante
        body = await request.json()
        message_data = whatsapp_business.process_webhook(body)
        
        if message_data.get("status") == "no_message":
            return PlainTextResponse("OK")
        
        if "error" in message_data:
            print(f"❌ Error procesando webhook: {message_data['error']}")
            return PlainTextResponse("Error", status_code=500)
        
        # Extraer información del mensaje
        user_number = message_data.get("from", "")
        user_message = message_data.get("text", "")
        message_type = message_data.get("type", "")
        
        print(f"📱 Mensaje WhatsApp Business recibido de {user_number}: {user_message}")
        
        # Cargar estado para obtener nombre
        state = load_conversation_state(user_number)
        user_name = state.get("name", "")
        
        # Procesar mensaje y obtener respuesta
        response_message = process_whatsapp_business_message(user_message, user_number, user_name)
        
        # Enviar respuesta
        if response_message:
            result = whatsapp_business.send_text_message(user_number, response_message)
            if result.get("status") == "success":
                print(f"✅ Respuesta WhatsApp Business enviada: {result.get('message_id')}")
            else:
                print("❌ Error enviando respuesta")
        
        return PlainTextResponse("OK")
        
    except Exception as e:
        print(f"Error en webhook WhatsApp Business: {e}")
        return PlainTextResponse("Error", status_code=500)

@app.get("/whatsapp/business/info")
async def get_whatsapp_business_info():
    """Obtiene información del número de WhatsApp Business"""
    try:
        result = whatsapp_business.get_phone_number_info()
        return result
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

@app.get("/whatsapp/business/templates")
async def get_whatsapp_business_templates():
    """Obtiene plantillas disponibles de WhatsApp Business"""
    try:
        result = whatsapp_business.get_templates()
        return result
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

@app.post("/whatsapp/bulk_send")
async def bulk_send_whatsapp(file: UploadFile = File(...)):
    """Envía mensajes de WhatsApp masivos desde archivo Excel"""
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            return {"error": "El archivo debe ser un Excel (.xlsx o .xls)"}
        
        # Leer archivo Excel
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        
        # Validar columnas requeridas
        required_columns = ['numero', 'mensaje']
        if not all(col in df.columns for col in required_columns):
            return {"error": f"El archivo debe contener las columnas: {required_columns}"}
        
        # Procesar contactos
        results = []
        success_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                # Obtener datos
                numero = str(row['numero']).strip()
                mensaje = str(row['mensaje']).strip()
                nombre = str(row.get('nombre', '')).strip() if 'nombre' in df.columns else ""
                
                # Limpiar número
                numero = re.sub(r'[^\d+]', '', numero)
                if not numero.startswith('+'):
                    numero = '+' + numero
                
                # Validar número
                digits_only = re.sub(r'[^\d]', '', numero)
                if len(digits_only) < 10:
                    results.append({
                        "row": index + 1,
                        "numero": numero,
                        "nombre": nombre,
                        "status": "error",
                        "error": "Número muy corto"
                    })
                    error_count += 1
                    continue
                
                # Enviar mensaje usando WhatsApp Business API
                result = send_whatsapp_business_message(numero, mensaje, nombre)
                
                if result.get("status") == "success":
                    results.append({
                        "row": index + 1,
                        "numero": numero,
                        "nombre": nombre,
                        "status": "enviado",
                        "message_id": result.get("message_id")
                    })
                    success_count += 1
                else:
                    results.append({
                        "row": index + 1,
                        "numero": numero,
                        "nombre": nombre,
                        "status": "error",
                        "error": result.get("error", "Error enviando mensaje")
                    })
                    error_count += 1
                
                # Pausa entre mensajes para evitar rate limits
                time.sleep(1)
                
            except Exception as e:
                results.append({
                    "row": index + 1,
                    "numero": str(row.get('numero', '')),
                    "nombre": str(row.get('nombre', '')),
                    "status": "error",
                    "error": str(e)
                })
                error_count += 1
        
        return {
            "message": f"Envio masivo completado. {success_count} mensajes enviados, {error_count} errores.",
            "total_contacts": len(df),
            "success_count": success_count,
            "error_count": error_count,
            "results": results
        }
        
    except Exception as e:
        return {"error": f"Error procesando archivo: {str(e)}"}

@app.post("/sendWhatsAppOnly")
async def send_whatsapp_only(file: UploadFile = File(...)):
    """Procesa archivo Excel con contactos y envía SOLO mensajes WhatsApp (sin llamadas)"""
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            return {"error": "El archivo debe ser un Excel (.xlsx o .xls)"}
        
        # Leer archivo Excel
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        
        # Validar columnas requeridas
        required_columns = ['numero']
        if not all(col in df.columns for col in required_columns):
            return {"error": f"El archivo debe contener las columnas: {required_columns}"}
        
        # Procesar contactos
        valid_contacts = []
        invalid_numbers = []
        results = []
        
        for index, row in df.iterrows():
            try:
                # Obtener número
                numero = str(row['numero']).strip()
                nombre = str(row.get('nombre', '')).strip() if 'nombre' in df.columns else ""
                
                # Limpiar número
                numero = re.sub(r'[^\d+]', '', numero)
                if not numero.startswith('+'):
                    numero = '+' + numero
                
                # Validar número (mínimo 10 dígitos)
                digits_only = re.sub(r'[^\d]', '', numero)
                if len(digits_only) < 10:
                    invalid_numbers.append({
                        "row": index + 1,
                        "numero": numero,
                        "nombre": nombre,
                        "error": "Número muy corto"
                    })
                    continue
                
                # ENVIAR SOLO MENSAJE DE WHATSAPP
                whatsapp_message = create_whatsapp_form_message("initial", nombre)
                whatsapp_result = send_whatsapp_business_message(numero, whatsapp_message, nombre)
                
                if whatsapp_result.get("status") == "success":
                    valid_contacts.append({
                        "numero": numero,
                        "nombre": nombre,
                        "whatsapp_message_id": whatsapp_result.get("message_id")
                    })
                    
                    results.append({
                        "numero": numero,
                        "nombre": nombre,
                        "status": "whatsapp_enviado",
                        "whatsapp_message_id": whatsapp_result.get("message_id")
                    })
                else:
                    invalid_numbers.append({
                        "row": index + 1,
                        "numero": numero,
                        "nombre": nombre,
                        "error": f"Error enviando WhatsApp: {whatsapp_result.get('error')}"
                    })
                
                # Pausa entre contactos para evitar rate limits
                time.sleep(1)
                
            except Exception as e:
                invalid_numbers.append({
                    "row": index + 1,
                    "numero": str(row.get('numero', '')),
                    "nombre": str(row.get('nombre', '')),
                    "error": str(e)
                })
        
        return {
            "message": f"Procesamiento completado. {len(valid_contacts)} mensajes WhatsApp enviados.",
            "total_contacts": len(df),
            "valid_contacts": len(valid_contacts),
            "invalid_contacts": len(invalid_numbers),
            "results": results,
            "invalid_numbers": invalid_numbers
        }
        
    except Exception as e:
        return {"error": f"Error procesando archivo: {str(e)}"}

@app.post("/whatsapp/documents")
async def receive_documents(request: Request):
    """Recibe documentos por WhatsApp y los procesa"""
    try:
        form = await request.form()
        user_number = form.get('from', '')
        cedula_name = form.get('cedula_name', '')
        recibo_name = form.get('recibo_name', '')
        email = form.get('email', '')
        
        # Limpiar número
        if not user_number.startswith('+'):
            user_number = '+' + user_number
        
        # Cargar estado
        state = load_conversation_state(user_number)
        user_name = state.get("name", "")
        
        # Verificar nombres
        names_match = verify_document_names(cedula_name, recibo_name)
        
        if names_match:
            # Enviar por correo
            email_result = send_documents_email(email, cedula_name, recibo_name, user_name)
            
            if email_result.get("status") == "success":
                response_message = f"""✅ ¡Perfecto {user_name}! 

He verificado tus documentos y los nombres coinciden perfectamente.

📧 He enviado tus documentos por correo electrónico.

📋 Próximos pasos:
1. ✅ Documentos verificados
2. 📊 Evaluación financiera en proceso
3. 📞 Confirmación de aprobación (24-48 horas)
4. 💰 Desembolso directo a tu cuenta

Te mantendré informado del proceso. ¡Gracias por confiar en AVANZA! 🎉"""
            else:
                response_message = f"""⚠️ {user_name}, hubo un problema enviando los documentos por correo.

Por favor, intenta enviarlos nuevamente o contáctanos directamente al +57 3014146715.

¡Gracias por tu paciencia! 📞"""
        else:
            response_message = f"""❌ {user_name}, he detectado una diferencia en los nombres de los documentos.

Por favor verifica que:
• El nombre en la cédula sea exactamente igual al del recibo de pago
• Los documentos estén legibles y completos

Una vez corregido, envíalos nuevamente. 📄"""
        
        # Enviar respuesta por WhatsApp
        whatsapp_result = send_whatsapp_business_message(user_number, response_message, user_name)
        
        # Actualizar estado
        if names_match:
            state["stage"] = "documents_verified"
            state["documents_sent"] = True
            state["email_sent"] = True
        else:
            state["stage"] = "waiting_documents"
        
        save_conversation_state(user_number, state)
        
        return {
            "status": "success",
            "names_match": names_match,
            "whatsapp_sent": whatsapp_result.get("status") == "success"
        }
        
    except Exception as e:
        return {"error": f"Error procesando documentos: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)
