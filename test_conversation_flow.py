#!/usr/bin/env python3
"""
Script de prueba para simular el flujo de conversación de WhatsApp
"""

import re
from datetime import datetime, timedelta
from typing import Optional

def get_current_time() -> datetime:
    """Obtiene la hora actual en zona horaria de Barranquilla"""
    import pytz
    barranquilla_tz = pytz.timezone('America/Bogota')
    return datetime.now(barranquilla_tz)

def parse_time_input(text: str) -> Optional[datetime]:
    """Parsea texto de tiempo del usuario y retorna datetime"""
    text = text.lower().strip()
    current_time = get_current_time()
    
    # Patrones comunes de tiempo
    patterns = [
        # "ahora", "ya", "inmediatamente", "ahora mismo"
        (r'\b(ahora|ya|inmediatamente|ahorita|ahora mismo)\b', lambda: current_time + timedelta(minutes=5)),
        
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

def simulate_conversation():
    """Simula el flujo de conversación"""
    
    # Estado inicial
    state = {
        "stage": "initial",
        "name": "Dylan",
        "messages_sent": 0,
        "last_interaction": get_current_time().isoformat()
    }
    
    print("🤖 Simulación de conversación con ANA")
    print("=" * 50)
    
    # Mensaje inicial
    initial_message = f"""¡Hola {state['name']}! 👋 Soy Ana, tu asesora de préstamos.

Te contacté porque fuiste pre-seleccionado para un préstamo especial de hasta $150 millones con tasas desde 1.6% mensual.

🎯 Beneficios exclusivos:
• Desembolso en 24-48 horas
• Solo necesitas cédula vigente
• Sin embargos
• Plazos flexibles

¿Te gustaría que te llame para explicarte todos los detalles? 

Responde con:
✅ "Sí, llámame" - Para que te llame ahora
⏰ "Llámame a las [hora]" - Para programar una llamada
❌ "No, gracias" - Para cerrar la conversación

¿Qué prefieres?"""
    
    print("📱 ANA:", initial_message)
    print()
    
    # Simular respuestas del usuario
    test_responses = [
        "Si, llámame",
        "Ahora mismo",
        "A las 3:30 PM",
        "En 2 horas",
        "Mañana a las 10:00"
    ]
    
    for i, user_response in enumerate(test_responses, 1):
        print(f"👤 Usuario: {user_response}")
        print()
        
        # Procesar respuesta según el estado
        user_response_lower = user_response.lower().strip()
        ai_reply = ""
        
        if state["stage"] == "initial":
            if any(word in user_response_lower for word in ["sí", "si", "llámame", "llamame", "llama", "ok", "okay", "claro", "ahora mismo"]):
                state["stage"] = "waiting_confirmation"
                ai_reply = f"""¡Perfecto {state['name']}! 

Para programar tu llamada y explicarte todos los detalles del préstamo, dime a qué hora te gustaría que te llame.

Ejemplos:
• "Ahora mismo" - Te llamo en 5 minutos
• "En 2 horas" - Te llamo en 2 horas
• "A las 3:30 PM" - Te llamo a esa hora
• "Mañana a las 10:00" - Te llamo mañana

¿Cuándo prefieres que te llame para revisar tu elegibilidad?"""
                
            elif any(word in user_response_lower for word in ["no", "gracias", "cancelar", "cerrar"]):
                state["stage"] = "completed"
                ai_reply = "Entendido. Gracias por tu tiempo. ¡Que tengas un excelente día! 😊"
                
            else:
                scheduled_time = parse_time_input(user_response)
                if scheduled_time:
                    state["stage"] = "scheduled_call"
                    state["scheduled_time"] = scheduled_time.isoformat()
                    state["call_scheduled"] = True
                    
                    ai_reply = f"""¡Perfecto {state['name']}! 

Tu llamada está programada para el {scheduled_time.strftime('%d/%m/%Y')} a las {scheduled_time.strftime('%H:%M')}.

Te llamaré puntualmente. Si necesitas cambiar la hora, solo dime "cambiar hora" y te ayudo a reprogramarla.

¿Hay algo más en lo que pueda ayudarte mientras tanto?"""
                else:
                    ai_reply = f"""Entiendo {state['name']}. 

Para ayudarte mejor, necesito que me digas específicamente:

✅ "Sí, llámame" - Para que te llame ahora
⏰ "Llámame a las [hora]" - Para programar una llamada
❌ "No, gracias" - Para cerrar la conversación

¿Qué prefieres?"""
        
        elif state["stage"] == "waiting_confirmation":
            scheduled_time = parse_time_input(user_response)
            
            if scheduled_time:
                state["stage"] = "scheduled_call"
                state["scheduled_time"] = scheduled_time.isoformat()
                state["call_scheduled"] = True
                
                if any(word in user_response_lower for word in ["ahora", "ya", "inmediatamente", "ahorita", "ahora mismo"]):
                    ai_reply = f"""¡Perfecto {state['name']}! 

Te llamaré en 5 minutos para explicarte todos los detalles del préstamo.

📋 En la llamada revisaremos:
• Tu situación actual
• Monto que puedes obtener
• Documentación necesaria
• Proceso de desembolso

¡Prepárate para la llamada! 📞"""
                else:
                    ai_reply = f"""¡Excelente {state['name']}! 

Tu llamada está programada para el {scheduled_time.strftime('%d/%m/%Y')} a las {scheduled_time.strftime('%H:%M')}.

Te llamaré puntualmente. Si necesitas cambiar la hora, solo dime "cambiar hora" y te ayudo a reprogramarla.

¿Hay algo más en lo que pueda ayudarte mientras tanto?"""
            else:
                ai_reply = f"""Entiendo {state['name']}. 

Para programar tu llamada, dime específicamente:
• "Ahora mismo" - Te llamo en 5 minutos
• "En 2 horas" - Te llamo en 2 horas
• "A las 3:30 PM" - Te llamo a esa hora
• "Mañana a las 10:00" - Te llamo mañana

¿Cuándo prefieres que te llame?"""
        
        elif state["stage"] == "scheduled_call":
            if any(word in user_response_lower for word in ["cambiar", "cambio", "otra hora", "diferente"]):
                state["stage"] = "waiting_confirmation"
                ai_reply = f"""¡Perfecto {state['name']}! 

Para programar tu llamada y explicarte todos los detalles del préstamo, dime a qué hora te gustaría que te llame.

Ejemplos:
• "Ahora mismo" - Te llamo en 5 minutos
• "En 2 horas" - Te llamo en 2 horas
• "A las 3:30 PM" - Te llamo a esa hora
• "Mañana a las 10:00" - Te llamo mañana

¿Cuándo prefieres que te llame para revisar tu elegibilidad?"""
            elif any(word in user_response_lower for word in ["cancelar", "no", "gracias"]):
                state["stage"] = "completed"
                ai_reply = "Entendido. He cancelado la llamada programada. ¡Que tengas un excelente día! 😊"
            else:
                ai_reply = f"""¡Excelente {state['name']}! 

Tu llamada está programada. Te llamaré puntualmente para revisar tu elegibilidad y explicarte todos los beneficios del préstamo.

📋 En la llamada revisaremos:
• Tu situación actual
• Monto que puedes obtener
• Documentación necesaria
• Proceso de desembolso

Si necesitas cambiar la hora, solo dime "cambiar hora" y te ayudo a reprogramarla.

¿Hay algo más en lo que pueda ayudarte mientras tanto?"""
        
        else:
            ai_reply = "Gracias por tu tiempo. ¡Que tengas un excelente día! 😊"
        
        print("📱 ANA:", ai_reply)
        print()
        print(f"🔍 Estado actual: {state['stage']}")
        if 'scheduled_time' in state:
            print(f"📅 Llamada programada: {state['scheduled_time']}")
        print("-" * 50)
        print()

if __name__ == "__main__":
    simulate_conversation() 