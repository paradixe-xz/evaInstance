#!/usr/bin/env python3
"""
Script de prueba para verificar la corrección del TTS
"""

import os
import sys
import uuid
from pydub import AudioSegment

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import generate_speech_elevenlabs

def test_tts_fix():
    """Prueba la función corregida de TTS"""
    print("🧪 Probando corrección del TTS...")
    
    # Crear directorio de audio si no existe
    os.makedirs("audio", exist_ok=True)
    
    # Texto de prueba
    test_text = "Hola, soy Ana tu asesora financiera de AVANZA. ¿Cómo estás?"
    test_filename = f"audio/test_tts_fix_{uuid.uuid4()}.wav"
    
    print(f"📝 Texto: {test_text}")
    print(f"🎵 Archivo: {test_filename}")
    
    # Generar audio
    success = generate_speech_elevenlabs(test_text, test_filename)
    
    if success:
        print("✅ Audio generado exitosamente")
        
        # Verificar que el archivo existe y tiene tamaño
        if os.path.exists(test_filename):
            file_size = os.path.getsize(test_filename)
            print(f"📊 Tamaño del archivo: {file_size} bytes")
            
            if file_size > 0:
                print("✅ Archivo válido generado")
                
                # Intentar cargar el archivo con pydub
                try:
                    audio = AudioSegment.from_wav(test_filename)
                    print(f"✅ Archivo WAV válido - Duración: {len(audio)/1000:.2f} segundos")
                    print(f"   Frecuencia: {audio.frame_rate} Hz")
                    print(f"   Canales: {audio.channels}")
                    print(f"   Ancho de muestra: {audio.sample_width * 8} bits")
                except Exception as e:
                    print(f"❌ Error cargando archivo WAV: {e}")
            else:
                print("❌ Archivo vacío")
        else:
            print("❌ Archivo no encontrado")
    else:
        print("❌ Error generando audio")
    
    return success

if __name__ == "__main__":
    test_tts_fix() 