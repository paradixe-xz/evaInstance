#!/usr/bin/env python3
"""
Script de prueba para verificar que el saludo se genera antes de la llamada
"""

import os
import sys
import uuid
import json
from datetime import datetime

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import schedule_call, load_conversation_state, generate_speech_elevenlabs

def test_pre_generated_greeting():
    """Prueba la generación de saludo antes de la llamada"""
    print("🧪 Probando generación de saludo antes de llamada...")
    
    # Crear directorio de audio si no existe
    os.makedirs("audio", exist_ok=True)
    
    # Número y nombre de prueba
    test_number = "+573013304134"
    test_name = "Dylan"
    
    print(f"📞 Número: {test_number}")
    print(f"👤 Nombre: {test_name}")
    
    # Simular la programación de llamada (sin hacer la llamada real)
    print("\n🎤 Generando saludo personalizado ANTES de la llamada...")
    
    # Generar saludo personalizado ANTES de la llamada
    greeting_text = (
        f"¡Alóoo {test_name}! ¿Cómo estás mi cielo? ¡Qué alegría saludarte! "
        f"Soy Ana tu asesora financiera de AVANZA y antes que nada gracias por responder nuestro mensajito. "
        f"Hoy no te estoy llamando para venderte un crédito —te lo prometo— sino para ayudarte a organizar tus finanzas "
        f"que es algo que todos necesitamos hoy en día ¿verdad? ¿Te agarré en un momento tranquilo? "
        f"Esto no toma más de 10 minuticos pero créeme pueden cambiar tu año."
    )
    greeting_filename = f"audio/greeting_{test_number.replace('+', '').replace('-', '')}_{uuid.uuid4()}.wav"
    
    print(f"📝 Texto del saludo: {greeting_text[:100]}...")
    print(f"🎵 Archivo: {greeting_filename}")
    
    # Generar audio
    success = generate_speech_elevenlabs(greeting_text, greeting_filename)
    
    if success:
        print("✅ Saludo generado exitosamente ANTES de la llamada")
        
        # Verificar que el archivo existe y tiene tamaño
        if os.path.exists(greeting_filename):
            file_size = os.path.getsize(greeting_filename)
            print(f"📊 Tamaño del archivo: {file_size} bytes")
            
            if file_size > 0:
                print("✅ Archivo de saludo válido generado")
                
                # Simular el estado que se guardaría
                from main import PUBLIC_BASE_URL
                greeting_url = f"{PUBLIC_BASE_URL}/audio/{os.path.basename(greeting_filename)}"
                
                print(f"🔗 URL del saludo: {greeting_url}")
                print(f"📁 Archivo guardado: {greeting_filename}")
                
                # Simular el estado que se guardaría en la conversación
                simulated_state = {
                    "stage": "call_in_progress",
                    "call_sid": "test_call_sid",
                    "call_started": True,
                    "call_status": "in_progress",
                    "name": test_name,
                    "greeting_audio_url": greeting_url,
                    "greeting_audio_file": greeting_filename
                }
                
                print("\n📋 Estado simulado de la conversación:")
                for key, value in simulated_state.items():
                    print(f"   {key}: {value}")
                
                print("\n✅ El saludo está listo para reproducirse inmediatamente cuando la persona conteste")
                print("🚀 ANA podrá hablar sin demoras porque el audio ya está generado")
                
                return True
            else:
                print("❌ Archivo vacío")
        else:
            print("❌ Archivo no encontrado")
    else:
        print("❌ Error generando saludo")
    
    return False

if __name__ == "__main__":
    test_pre_generated_greeting() 