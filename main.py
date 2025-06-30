from fastapi import FastAPI, HTTPException, Request, Form
from pydantic import BaseModel
from typing import List
import os
import subprocess
from twilio.rest import Client
from fastapi.responses import Response, PlainTextResponse
from twilio.twiml.voice_response import VoiceResponse
import ollama  # Para usar el modelo de chat

app = FastAPI()

# Twilio config (solo variables de entorno, sin valores hardcodeados)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')
TWILIO_WEBHOOK_URL = os.getenv('TWILIO_WEBHOOK_URL')
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.get("/")
def read_root():
    return {"Hello": "World"}

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
    # This endpoint is called by Twilio when the call is answered
    # Here, you would connect the call to the AI assistant logic
    # For now, just greet and say "Connecting you to the AI assistant"
    response = VoiceResponse()
    response.say("Connecting you to the AI assistant.")
    # TODO: Stream call audio to/from AI assistant (see app.py for logic)
    # This is a placeholder; actual media streaming requires Twilio Media Streams and websocket handling
    response.say("Sorry, the AI assistant is not available yet.")
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
    # Formato: alterna 'user:' y 'assistant:'
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
        # El número viene como 'whatsapp:+1234567890', extraer solo el número
        if from_number.startswith('whatsapp:'):
            user_number = from_number.replace('whatsapp:', '')
        else:
            user_number = from_number
        print("User number:", user_number)
        # Cargar historial
        history = load_history(user_number)
        print("Historial cargado:", history)
        # Agregar mensaje del usuario
        append_to_history(user_number, 'user', body)
        history.append({'role': 'user', 'content': body})
        # Llamar al modelo (ollama)
        try:
            response = ollama.chat(
                model='isa',  # O el modelo que prefieras
                messages=history
            )
            ai_reply = response['message']['content']
        except Exception as e:
            print("Error llamando a ollama:", e)
            ai_reply = "Lo siento, hubo un error procesando tu mensaje."
        # Guardar respuesta de la IA
        append_to_history(user_number, 'assistant', ai_reply)
        # Responder por WhatsApp
        client.messages.create(
            body=ai_reply,
            from_="whatsapp:" + TWILIO_WHATSAPP_NUMBER,
            to="whatsapp:" + user_number
        )
        print("Respuesta enviada por WhatsApp")
        return PlainTextResponse("OK")
    except Exception as e:
        print("Error general en el endpoint:", e)
        return PlainTextResponse("Error interno en el servidor", status_code=500)
