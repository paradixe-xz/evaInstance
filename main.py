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

app = FastAPI()

# Configuración de zona horaria (Barranquilla, Colombia)
TIMEZONE = pytz.timezone('America/Bogota')  # Barranquilla usa la misma zona que Bogotá

# Twilio config (solo variables de entorno, sin valores hardcodeados)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')
TWILIO_WEBHOOK_URL = os.getenv('TWILIO_WEBHOOK_URL')

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
    """Programa una llamada inmediata para un contacto"""
    try:
        print(f"Programando llamada inmediata para {number} ({name})")
        call = client.calls.create(
            to=number,
            from_=TWILIO_PHONE_NUMBER,
            url=TWILIO_WEBHOOK_URL
        )
        print(f"Llamada iniciada: {call.sid}")
        
        # Actualizar estado
        state = load_conversation_state(number)
        state["stage"] = "call_in_progress"
        state["call_sid"] = call.sid
        state["call_started"] = True
        state["call_status"] = "in_progress"
        state["name"] = name
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

def generate_speech_elevenlabs(text, output_file):
    """Genera audio usando ElevenLabs y lo convierte a WAV 8kHz mono para Twilio"""
    try:
        if not elevenlabs_client:
            print("Error: ElevenLabs client no configurado")
            return False
            
        # Generar audio con ElevenLabs usando el nuevo API
        audio = elevenlabs_client.text_to_speech.convert(
            text=text,
            voice_id=ELEVENLABS_VOICE_ID,
            model_id="eleven_multilingual_v2"
        )
        
        # Guardar temporalmente - el audio es un generador, necesitamos iterarlo
        temp_file = output_file + ".temp.wav"
        with open(temp_file, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        
        # Convertir a WAV 8kHz mono para Twilio
        audio_segment = AudioSegment.from_wav(temp_file)
        audio_segment = audio_segment.set_frame_rate(8000).set_channels(1)
        audio_segment.export(output_file, format="wav")
        
        # Limpiar archivo temporal
        os.remove(temp_file)
        
        return True
        
    except Exception as e:
        print(f"Error generando audio con ElevenLabs: {e}")
        return False

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
    
    # Generar saludo personalizado con ElevenLabs siguiendo el guion de 10 minutos
    greeting_text = (
        f"¡Alóoo {user_name}! ¿Cómo estás mi cielo? ¡Qué alegría saludarte! "
        f"Soy Ana tu asesora financiera de AVANZA y antes que nada gracias por responder nuestro mensajito. "
        f"Hoy no te estoy llamando para venderte un crédito —te lo prometo— sino para ayudarte a organizar tus finanzas "
        f"que es algo que todos necesitamos hoy en día ¿verdad? ¿Te agarré en un momento tranquilo? "
        f"Esto no toma más de 10 minuticos pero créeme pueden cambiar tu año."
    )
    greeting_filename = f"audio/greeting_{uuid.uuid4()}.wav"
    
    print("Generando saludo personalizado con ElevenLabs...")
    if generate_speech_elevenlabs(greeting_text, greeting_filename):
        greeting_url = f"{PUBLIC_BASE_URL}/audio/{os.path.basename(greeting_filename)}"
        print(f"Saludo generado exitosamente: {greeting_url}")
        response.play(greeting_url)
    else:
        print("Error generando saludo, usando fallback")
        response.say(
            f"¡Alóoo {user_name}! ¿Cómo estás mi cielo? ¡Qué alegría saludarte! "
            "Soy Ana tu asesora financiera de AVANZA y antes que nada gracias por responder nuestro mensajito. "
            "Hoy no te estoy llamando para venderte un crédito —te lo prometo— sino para ayudarte a organizar tus finanzas "
            "que es algo que todos necesitamos hoy en día ¿verdad? ¿Te agarré en un momento tranquilo? "
            "Esto no toma más de 10 minuticos pero créeme pueden cambiar tu año.",
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
    
    # Generar respuesta de IA
    try:
        # Crear historial de conversación para IA
        history = []
        for entry in transcript_data["conversation"]:
            history.append({
                'role': entry['role'],
                'content': entry['content']
            })
        
        response_ia = ollama.chat(
            model='ana',
            messages=history
        )
        ai_reply = response_ia['message']['content']
        
    except Exception as e:
        print("Error llamando a ollama:", e)
        ai_reply = "Lo siento, hubo un error procesando tu mensaje."
    
    # Agregar respuesta de IA a la transcripción
    transcript_data["conversation"].append({
        "role": "assistant",
        "content": ai_reply,
        "timestamp": get_current_time().isoformat()
    })
    
    # Guardar transcripción actualizada
    save_transcript(user_number, transcript_data)
    
    # Usar ElevenLabs TTS
    audio_filename = f"audio/response_{uuid.uuid4()}.wav"
    response = VoiceResponse()
    print(f"Generando audio para: {ai_reply[:50]}...")
    
    if generate_speech_elevenlabs(ai_reply, audio_filename):
        audio_url = f"{PUBLIC_BASE_URL}/audio/{os.path.basename(audio_filename)}"
        print(f"Audio generado exitosamente: {audio_url}")
        response.play(audio_url)
    else:
        print("Error generando audio, usando fallback")
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
        state["stage"] = "analyzed"
        
        # Determinar si necesita seguimiento humano
        if analysis.get("human_followup_needed", False) or analysis.get("interest_level") in ["high", "medium"]:
            state["stage"] = "ready_for_human"
        
        save_conversation_state(user_number, state)
        
        print(f"Análisis completado para {user_number}: {analysis.get('interest_level', 'unknown')} interés")
    
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
    """Procesa archivo Excel con contactos y hace llamadas directas"""
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
                
                # Programar llamada inmediata
                call_sid = schedule_call(numero, nombre)
                
                if call_sid:
                    valid_contacts.append({
                        "numero": numero,
                        "nombre": nombre,
                        "call_sid": call_sid
                    })
                    
                    results.append({
                        "numero": numero,
                        "nombre": nombre,
                        "status": "llamada_programada",
                        "call_sid": call_sid
                    })
                else:
                    invalid_numbers.append({
                        "row": index + 1,
                        "numero": numero,
                        "nombre": nombre,
                        "error": "Error programando llamada"
                    })
                
            except Exception as e:
                invalid_numbers.append({
                    "row": index + 1,
                    "numero": str(row.get('numero', '')),
                    "nombre": str(row.get('nombre', '')),
                    "error": str(e)
                })
        
        return {
            "message": f"Procesamiento completado. {len(valid_contacts)} llamadas programadas.",
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
