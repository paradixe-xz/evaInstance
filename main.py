from fastapi import FastAPI, HTTPException, Request, Form
from pydantic import BaseModel
from typing import List
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
from elevenlabs import generate, save, set_api_key, voices

app = FastAPI()

# Twilio config (solo variables de entorno, sin valores hardcodeados)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')
TWILIO_WEBHOOK_URL = os.getenv('TWILIO_WEBHOOK_URL')

# ElevenLabs config
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')  # Rachel voice

if ELEVENLABS_API_KEY:
    set_api_key(ELEVENLABS_API_KEY)

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Crea el directorio de audios si no existe
audio_dir = "audio"
os.makedirs(audio_dir, exist_ok=True)
app.mount("/audio", StaticFiles(directory=audio_dir), name="audio")

# Obtén la URL base pública desde el entorno
PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL', '')

def generate_speech_elevenlabs(text, output_file):
    """Genera audio usando ElevenLabs y lo convierte a WAV 8kHz mono para Twilio"""
    try:
        if not ELEVENLABS_API_KEY:
            print("Error: ELEVENLABS_API_KEY no configurada")
            return False
            
        # Generar audio con ElevenLabs
        audio = generate(
            text=text,
            voice=ELEVENLABS_VOICE_ID,
            model="eleven_multilingual_v2"
        )
        
        # Guardar temporalmente
        temp_file = output_file + ".temp.wav"
        save(audio, temp_file)
        
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

# --- Nuevo endpoint para recibir números de teléfono ---
class PhoneNumbersRequest(BaseModel):
    numbers: List[str]

@app.post("/sendNumbers")
def send_numbers(req: PhoneNumbersRequest):
    print("Números recibidos:", req.numbers)
    try:
        results = []
        for number in req.numbers:
            # Enviar mensaje de WhatsApp
            whatsapp_message = client.messages.create(
                body="Hola",
                from_="whatsapp:" + TWILIO_WHATSAPP_NUMBER,
                to="whatsapp:" + number
            )
            # Iniciar llamada
            call = client.calls.create(
                to=number,
                from_=TWILIO_PHONE_NUMBER,
                url=TWILIO_WEBHOOK_URL
            )
            results.append({
                "to": number,
                "whatsapp_sid": whatsapp_message.sid,
                "call_sid": call.sid
            })
        return {"message": "Mensajes y llamadas iniciados correctamente", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando los números: {e}")

@app.post("/twilio/voice")
async def twilio_voice(request: Request):
    response = VoiceResponse()
    response.say("Hola, estás hablando con la IA. Por favor, di algo después del beep y espera la respuesta.", language="es-ES")
    response.gather(
        input="speech",
        language="es-ES",
        action="/twilio/voice/handle_speech",
        method="POST",
        timeout=7,
        speechTimeout="auto"
    )
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
            model='isa',
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
    print("¡Llego un mensaje de Twilio!")
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
        history = load_history(user_number)
        print("Historial cargado:", history)
        append_to_history(user_number, 'user', body)
        history.append({'role': 'user', 'content': body})
        try:
            response = ollama.chat(
                model='isa',
                messages=history
            )
            ai_reply = response['message']['content']
        except Exception as e:
            print("Error llamando a ollama:", e)
            ai_reply = "Lo siento, hubo un error procesando tu mensaje."
        append_to_history(user_number, 'assistant', ai_reply)
        client.messages.create(
            body=ai_reply,
            from_="whatsapp:" + TWILIO_WHATSAPP_NUMBER,
            to="whatsapp:" + user_number
        )
        print("Respuesta enviada por WhatsApp")
    except Exception as e:
        print("Error general en el endpoint:", e)
        return PlainTextResponse("Error interno en el servidor", status_code=500)
