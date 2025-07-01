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
        "stage": "initial",  # initial, waiting_confirmation, scheduled_call, completed
        "name": "",
        "scheduled_time": None,
        "call_scheduled": False,
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

def get_current_time() -> datetime:
    """Obtiene la hora actual en Barranquilla"""
    return datetime.now(TIMEZONE)

def parse_time_input(text: str) -> Optional[datetime]:
    """Parsea texto de tiempo del usuario y retorna datetime"""
    text = text.lower().strip()
    current_time = get_current_time()
    
    # Patrones comunes de tiempo
    patterns = [
        # "ahora", "ya", "inmediatamente", "ahora mismo"
        (r'\b(ahora|ya|inmediatamente|ahorita|ahora mismo)\b', lambda m: current_time + timedelta(minutes=1)),
        
        # "en X minutos"
        (r'en (\d+) minutos?', lambda m: current_time + timedelta(minutes=int(m.group(1)))),
        
        # "en X horas"
        (r'en (\d+) horas?', lambda m: current_time + timedelta(hours=int(m.group(1)))),
        
        # "a las X:Y" (formato 24h)
        (r'a las (\d{1,2}):(\d{2})', lambda m: current_time.replace(
            hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0
        )),
        
        # "a las X:Y AM/PM" (formato 12h)
        (r'a las (\d{1,2}):(\d{2})\s*(am|pm)', lambda m: 
            current_time.replace(
                hour=int(m.group(1)) + (12 if m.group(3) == 'pm' and int(m.group(1)) != 12 else 0),
                minute=int(m.group(2)), second=0, microsecond=0
            )
        ),
        
        # "mañana a las X:Y"
        (r'mañana a las (\d{1,2}):(\d{2})', lambda m: 
            (current_time + timedelta(days=1)).replace(
                hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0
            )
        ),
    ]
    
    for pattern, time_func in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return time_func(match) if callable(time_func) else time_func()
            except Exception as e:
                print(f"Error parseando tiempo: {e}")
                continue
    
    return None

def schedule_call(number: str, scheduled_time: datetime, name: str):
    """Programa una llamada para un tiempo específico"""
    job_id = f"call_{number}_{scheduled_time.strftime('%Y%m%d_%H%M%S')}"
    
    def make_call():
        try:
            print(f"Ejecutando llamada programada para {number} ({name})")
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
            save_conversation_state(number, state)
            
        except Exception as e:
            print(f"Error ejecutando llamada programada para {number}: {e}")
    
    scheduler.add_job(
        func=make_call,
        trigger=DateTrigger(run_date=scheduled_time),
        id=job_id,
        replace_existing=True
    )
    
    print(f"Llamada programada para {number} a las {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}")

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

Responde con:
✅ "Sí" - Te llamo inmediatamente
❌ "No" - Para escoger otra hora
⏰ "Llámame a las [hora]" - Te llamo cuando quieras

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
        audio_segment = AudioSegment.from_file(temp_file)
        audio_segment = audio_segment.set_frame_rate(8000).set_channels(1)
        audio_segment.export(output_file, format="wav")
        
        # Limpiar archivo temporal
        os.remove(temp_file)
        
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            print(f"Audio generado con ElevenLabs: {output_file}")
            return True
        else:
            print("Archivo de audio no se creó correctamente")
            return False
    except Exception as e:
        print(f"Error generando audio con ElevenLabs: {e}")
        return False

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/test-tts")
def test_tts():
    """Endpoint para probar el TTS"""
    test_text = "Hola, esto es una prueba del sistema de voz con ElevenLabs."
    audio_filename = f"audio/test_{uuid.uuid4()}.wav"
    
    print(f"Probando ElevenLabs TTS con texto: {test_text}")
    
    if generate_speech_elevenlabs(test_text, audio_filename):
        audio_url = f"{PUBLIC_BASE_URL}/audio/{os.path.basename(audio_filename)}"
        return {
            "success": True,
            "message": "ElevenLabs TTS funcionando correctamente",
            "audio_url": audio_url,
            "voice_id": ELEVENLABS_VOICE_ID,
            "text": test_text
        }
    else:
        return {
            "success": False,
            "message": "Error en ElevenLabs TTS",
            "voice_id": ELEVENLABS_VOICE_ID,
            "text": test_text
        }

# --- Endpoint para crear representante (original) ---
class CreateRepresentativeRequest(BaseModel):
    model_name: str
    from_model: str
    temperature: float
    num_ctx: int
    system_prompt: str

@app.post("/createRepresentative")
def create_representative(req: CreateRepresentativeRequest):
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)
    modelfile_path = os.path.join(models_dir, f"{req.model_name}.Modelfile")
    try:
        with open(modelfile_path, "w") as f:
            f.write(f"FROM {req.from_model}\n\n")
            f.write(f"PARAMETER temperature {req.temperature}\n")
            f.write(f"PARAMETER num_ctx {req.num_ctx}\n\n")
            f.write(f'SYSTEM """\n{req.system_prompt}\n"""\n')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating Modelfile: {e}")

    # Run ollama create command
    try:
        result = subprocess.run(
            ["ollama", "create", req.model_name, "-f", modelfile_path],
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error running ollama create: {e.stderr}")

    return {"message": f"Representative '{req.model_name}' created successfully.", "output": result.stdout}

# --- Nuevo endpoint para recibir archivo Excel con nombres y números ---
@app.post("/sendNumbers")
async def send_numbers(file: UploadFile = File(...)):
    print(f"Archivo recibido: {file.filename}")
    
    # Validar que sea un archivo Excel
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
    
    try:
        # Leer el contenido del archivo
        content = await file.read()
        
        # Procesar el archivo Excel
        try:
            df = pd.read_excel(io.BytesIO(content))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error leyendo el archivo Excel: {str(e)}")
        
        # Validar que tenga las columnas necesarias
        required_columns = ['nombre', 'numero']
        missing_columns = [col for col in required_columns if col.lower() not in [col.lower() for col in df.columns]]
        
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"El archivo debe contener las columnas: {', '.join(required_columns)}. Columnas faltantes: {', '.join(missing_columns)}"
            )
        
        # Normalizar nombres de columnas
        df.columns = df.columns.str.lower()
        
        # Limpiar datos
        df = df.dropna(subset=['numero'])  # Eliminar filas sin número
        df['numero'] = df['numero'].astype(str).str.strip()
        
        # Validar números de teléfono
        valid_numbers = []
        invalid_numbers = []
        
        for index, row in df.iterrows():
            number = row['numero']
            name = row.get('nombre', 'Sin nombre')
            
            # Limpiar número (remover espacios, guiones, etc.)
            clean_number = ''.join(filter(str.isdigit, number))
            
            # Validar formato básico
            if len(clean_number) >= 10:
                # Agregar + si no tiene
                if not clean_number.startswith('+'):
                    clean_number = '+' + clean_number
                valid_numbers.append({
                    'name': name,
                    'number': clean_number,
                    'original_number': number
                })
            else:
                invalid_numbers.append({
                    'name': name,
                    'number': number,
                    'row': index + 2  # +2 porque Excel empieza en 1 y tenemos header
                })
        
        if not valid_numbers:
            raise HTTPException(status_code=400, detail="No se encontraron números de teléfono válidos en el archivo")
        
        # Procesar números válidos
        results = []
        for contact in valid_numbers:
            try:
                # Inicializar estado de conversación
                state = load_conversation_state(contact['number'])
                state["name"] = contact['name']
                state["stage"] = "initial"
                state["last_interaction"] = get_current_time().isoformat()
                save_conversation_state(contact['number'], state)
                
                # Enviar mensaje inicial de WhatsApp con formulario
                initial_message = create_whatsapp_form_message("initial", contact['name'])
                whatsapp_message = client.messages.create(
                    body=initial_message,
                    from_="whatsapp:" + TWILIO_WHATSAPP_NUMBER,
                    to="whatsapp:" + contact['number']
                )
                
                results.append({
                    "name": contact['name'],
                    "to": contact['number'],
                    "whatsapp_sid": whatsapp_message.sid,
                    "status": "initial_message_sent",
                    "message": "Mensaje inicial enviado - esperando confirmación del usuario"
                })
                
            except Exception as e:
                results.append({
                    "name": contact['name'],
                    "to": contact['number'],
                    "error": str(e),
                    "status": "error"
                })
        
        return {
            "message": f"Procesamiento completado. {len(valid_numbers)} contactos válidos encontrados.",
            "total_contacts": len(df),
            "valid_contacts": len(valid_numbers),
            "invalid_contacts": len(invalid_numbers),
            "results": results,
            "invalid_numbers": invalid_numbers
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando el archivo: {str(e)}")

@app.get("/conversations/status")
def get_conversations_status():
    """Endpoint para ver el estado de todas las conversaciones"""
    try:
        conversations = []
        current_time = get_current_time()
        
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
                        "name": state.get("name", "Sin nombre"),
                        "stage": state.get("stage", "unknown"),
                        "messages_sent": state.get("messages_sent", 0),
                        "call_scheduled": state.get("call_scheduled", False),
                        "scheduled_time": state.get("scheduled_time"),
                        "last_interaction": state.get("last_interaction"),
                        "time_since_last_interaction": str(time_diff).split('.')[0] if time_diff.total_seconds() > 0 else "Ahora mismo"
                    })
                except Exception as e:
                    print(f"Error leyendo conversación {filename}: {e}")
                    continue
        
        # Ordenar por última interacción (más reciente primero)
        conversations.sort(key=lambda x: x["last_interaction"], reverse=True)
        
        return {
            "total_conversations": len(conversations),
            "current_time": current_time.isoformat(),
            "timezone": str(TIMEZONE),
            "conversations": conversations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado de conversaciones: {str(e)}")

@app.post("/twilio/voice")
async def twilio_voice(request: Request):
    response = VoiceResponse()
    
    # Obtener el número del usuario
    form = await request.form()
    from_number = form.get('From', '')
    
    if from_number.startswith('whatsapp:'):
        user_number = from_number.replace('whatsapp:', '').strip()
    else:
        user_number = from_number.strip()
    
    if not user_number.startswith('+'):
        user_number = '+' + user_number
    
    # Cargar estado de conversación para obtener el nombre
    state = load_conversation_state(user_number)
    user_name = state.get("name", "mi cielo")
    
    # Generar saludo personalizado con ElevenLabs siguiendo el guion de 10 minutos
    greeting_text = (
        f"¡Alóoo, {user_name}! ¿Cómo estás, mi cielo? ¡Qué alegría saludarte! "
        f"Soy Ana, tu asesora financiera de AVANZA, y antes que nada, gracias por responder nuestro mensajito. "
        f"Hoy no te estoy llamando para venderte un crédito —te lo prometo—, sino para ayudarte a organizar tus finanzas, "
        f"que es algo que todos necesitamos hoy en día, ¿verdad? ¿Te agarré en un momento tranquilo? "
        f"Esto no toma más de 10 minuticos, pero créeme: pueden cambiar tu año."
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
            f"¡Alóoo, {user_name}! ¿Cómo estás, mi cielo? ¡Qué alegría saludarte! "
            "Soy Ana, tu asesora financiera de AVANZA, y antes que nada, gracias por responder nuestro mensajito. "
            "Hoy no te estoy llamando para venderte un crédito —te lo prometo—, sino para ayudarte a organizar tus finanzas, "
            "que es algo que todos necesitamos hoy en día, ¿verdad? ¿Te agarré en un momento tranquilo? "
            "Esto no toma más de 10 minuticos, pero créeme: pueden cambiar tu año.",
            language="es-ES"
        )
    
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
    form = await request.form()
    speech_result = form.get('SpeechResult', '').strip()
    from_number = form.get('From', '')
    print(f"SpeechResult: {speech_result}")
    print(f"From: {from_number}")
    user_number = from_number.replace('whatsapp:', '').strip()
    if not user_number.startswith('+'):
        user_number = '+' + user_number
    history = load_history(user_number)
    append_to_history(user_number, 'user', speech_result)
    history.append({'role': 'user', 'content': speech_result})
    try:
        response_ia = ollama.chat(
            model='ana',
            messages=history
        )
        ai_reply = response_ia['message']['content']
    except Exception as e:
        print("Error llamando a ollama:", e)
        ai_reply = "Lo siento, hubo un error procesando tu mensaje."
    append_to_history(user_number, 'assistant', ai_reply)
    
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

# --- Endpoint webhook para WhatsApp (Twilio) ---
@app.post("/twilio/whatsapp")
async def whatsapp_webhook(request: Request):
    print("¡Llego un mensaje de WhatsApp!")
    try:
        form = await request.form()
        print("Form recibido:", form)
        from_number = form.get('From', '')
        body = form.get('Body', '').strip()
        print("From:", from_number, "Body:", body)
        
        if from_number.startswith('whatsapp:'):
            user_number = from_number.replace('whatsapp:', '').strip()
        else:
            user_number = from_number.strip()
        
        if not user_number.startswith('+'):
            user_number = '+' + user_number
        
        print("User number:", user_number)
        
        # Cargar estado de conversación
        state = load_conversation_state(user_number)
        state["last_interaction"] = get_current_time().isoformat()
        state["messages_sent"] += 1
        
        # Procesar respuesta según el estado actual
        user_response = body.lower().strip()
        ai_reply = ""
        
        if state["stage"] == "initial":
            # Primera interacción - procesar respuesta inicial
            if any(word in user_response for word in ["sí", "si", "llámame", "llamame", "llama", "ok", "okay", "claro", "ahora mismo", "ya", "inmediatamente", "ahorita", "perfecto", "dale", "vamos", "puedes", "adelante"]):
                # Usuario quiere que lo llame ahora - llamar inmediatamente
                print(f"¡Usuario {state['name']} dice que SÍ! Programando llamada inmediata...")
                scheduled_time = get_current_time() + timedelta(minutes=1)
                state["stage"] = "scheduled_call"
                state["scheduled_time"] = scheduled_time.isoformat()
                state["call_scheduled"] = True
                
                # Programar llamada
                schedule_call(user_number, scheduled_time, state["name"])
                
                ai_reply = f"""🚀 ¡Perfecto {state['name']}! 

Te llamaré inmediatamente para explicarte todos los detalles del préstamo AVANZA.

📋 En la llamada de 10 minutos revisaremos:
• Tu situación actual y capacidad de pago
• Cómo podemos bajarte esa cuota que te tiene apretado
• Monto que puedes obtener (hasta $150 millones)
• Documentación necesaria (solo cédula vigente)
• Proceso de desembolso (24-48 horas)

¡Prepárate para mejorar tu salud financiera! 💰💪📞"""
                
            elif any(word in user_response for word in ["no", "gracias", "cancelar", "cerrar", "no ahora", "después", "más tarde", "ahora no", "no puedo"]):
                # Usuario no quiere llamada ahora - permitir escoger hora
                state["stage"] = "waiting_confirmation"
                ai_reply = f"""Entiendo {state['name']}. 

¿Cuándo te viene mejor para que te llame?

⏰ Opciones:
• "Ahora mismo" - Te llamo inmediatamente
• "En 2 horas" - Te llamo en 2 horas  
• "A las 3:30 PM" - Te llamo a esa hora
• "Mañana a las 10:00" - Te llamo mañana
• "No, gracias" - Para cerrar la conversación

¿Cuándo te parece mejor? 💰"""
                
            else:
                # Buscar si menciona una hora específica
                scheduled_time = parse_time_input(user_response)
                if scheduled_time:
                    state["stage"] = "scheduled_call"
                    state["scheduled_time"] = scheduled_time.isoformat()
                    state["call_scheduled"] = True
                    
                    # Programar llamada
                    schedule_call(user_number, scheduled_time, state["name"])
                    
                    ai_reply = f"""¡Perfecto {state['name']}! 

Tu llamada está programada para el {scheduled_time.strftime('%d/%m/%Y')} a las {scheduled_time.strftime('%H:%M')}.

Te llamaré puntualmente. Si necesitas cambiar la hora, solo dime "cambiar hora" y te ayudo a reprogramarla.

¿Hay algo más en lo que pueda ayudarte mientras tanto?"""
                else:
                    # Respuesta no reconocida - ser más específico
                    ai_reply = f"""Entiendo {state['name']}. 

Para ayudarte mejor, necesito que me digas específicamente:

✅ "Sí" - Para que te llame inmediatamente
❌ "No" - Para escoger otra hora
⏰ "Llámame a las [hora]" - Para programar una llamada

¿Qué prefieres?"""
        
        elif state["stage"] == "waiting_confirmation":
            # Usuario confirmó que quiere llamada - procesar hora
            scheduled_time = parse_time_input(user_response)
            
            if scheduled_time:
                state["stage"] = "scheduled_call"
                state["scheduled_time"] = scheduled_time.isoformat()
                state["call_scheduled"] = True
                
                # Programar llamada
                schedule_call(user_number, scheduled_time, state["name"])
                
                # Si es "ahora mismo", dar respuesta inmediata
                if any(word in user_response.lower() for word in ["ahora", "ya", "inmediatamente", "ahorita", "ahora mismo"]):
                    ai_reply = f"""🚀 ¡Perfecto {state['name']}! 

Te llamaré inmediatamente para explicarte todos los detalles del préstamo AVANZA.

📋 En la llamada de 10 minutos revisaremos:
• Tu situación actual y capacidad de pago
• Cómo podemos bajarte esa cuota que te tiene apretado
• Monto que puedes obtener (hasta $150 millones)
• Documentación necesaria (solo cédula vigente)
• Proceso de desembolso (24-48 horas)

¡Prepárate para mejorar tu salud financiera! 💰💪📞"""
                else:
                    ai_reply = f"""✅ ¡Excelente {state['name']}! 

Tu llamada está programada para el {scheduled_time.strftime('%d/%m/%Y')} a las {scheduled_time.strftime('%H:%M')}.

Te llamaré puntualmente para revisar tu elegibilidad y explicarte todos los beneficios del préstamo AVANZA.

Si necesitas cambiar la hora, solo dime "cambiar hora" y te ayudo a reprogramarla.

¡Prepárate para mejorar tu salud financiera! 💰💪"""
            else:
                # Si no reconoce el tiempo, dar opciones más claras
                ai_reply = f"""💡 Entiendo {state['name']}. 

Para agendar tu llamada y revisar tu elegibilidad, dime específicamente:
• "Ahora mismo" - Te llamo inmediatamente
• "En 2 horas" - Te llamo en 2 horas
• "A las 3:30 PM" - Te llamo a esa hora
• "Mañana a las 10:00" - Te llamo mañana

¿Cuándo te viene mejor para revisar tu situación y calcular tu préstamo? 💰"""
        
        elif state["stage"] == "scheduled_call":
            # Llamada ya programada - verificar si quiere cambiar hora
            if any(word in user_response for word in ["cambiar", "cambio", "otra hora", "diferente"]):
                state["stage"] = "waiting_confirmation"
                ai_reply = create_whatsapp_form_message("waiting_confirmation", state["name"])
            elif any(word in user_response for word in ["cancelar", "no", "gracias"]):
                state["stage"] = "completed"
                ai_reply = "Entendido. He cancelado la llamada programada. ¡Que tengas un excelente día! 😊"
            else:
                ai_reply = create_whatsapp_form_message("scheduled_call", state["name"])
        
        else:
            # Estado completado o desconocido
            ai_reply = "Gracias por tu tiempo. ¡Que tengas un excelente día! 😊"
        
        # Guardar estado actualizado
        save_conversation_state(user_number, state)
        
        # Guardar en historial para IA
        append_to_history(user_number, 'user', body)
        append_to_history(user_number, 'assistant', ai_reply)
        
        # Enviar respuesta
        client.messages.create(
            body=ai_reply,
            from_="whatsapp:" + TWILIO_WHATSAPP_NUMBER,
            to="whatsapp:" + user_number
        )
        
        print(f"Respuesta enviada por WhatsApp a {user_number}: {ai_reply[:50]}...")
        
    except Exception as e:
        print("Error general en el endpoint:", e)
        return PlainTextResponse("Error interno en el servidor", status_code=500)
