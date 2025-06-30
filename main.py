from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List
import os
import subprocess
from twilio.rest import Client
from fastapi.responses import Response, PlainTextResponse
from twilio.twiml.voice_response import VoiceResponse

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
