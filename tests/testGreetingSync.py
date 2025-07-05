#!/usr/bin/env python3
"""
Script de prueba para verificar la sincronización del saludo pre-generado
"""

import requests
import time
import json
import os
from datetime import datetime

def test_greeting_synchronization():
    """Prueba la sincronización del saludo pre-generado"""
    
    base_url = "http://localhost:4000"
    
    print("🧪 Probando sincronización de saludos pre-generados...")
    
    # 1. Programar una llamada (esto debería generar el saludo)
    test_number = "+573001234567"
    test_name = "Juan Pérez"
    
    print(f"📞 Programando llamada para {test_name} ({test_number})...")
    
    try:
        # Simular programación de llamada
        response = requests.post(f"{base_url}/schedule_call", json={
            "number": test_number,
            "name": test_name
        })
        
        if response.status_code == 200:
            print("✅ Llamada programada exitosamente")
            
            # 2. Verificar que se creó el estado de conversación
            conversation_file = f"conversations/conversation-{test_number}.json"
            if os.path.exists(conversation_file):
                with open(conversation_file, 'r') as f:
                    state = json.load(f)
                
                print(f"📋 Estado de conversación:")
                print(f"  - Generación iniciada: {state.get('greeting_generation_started', False)}")
                print(f"  - Saludo listo: {state.get('greeting_ready', False)}")
                print(f"  - Fallback: {state.get('greeting_fallback', False)}")
                print(f"  - Archivo: {state.get('greeting_audio_file', 'No especificado')}")
                
                # 3. Esperar a que se complete la generación
                max_wait = 15
                wait_time = 0
                print(f"⏳ Esperando hasta {max_wait} segundos para que se complete la generación...")
                
                while wait_time < max_wait:
                    time.sleep(1)
                    wait_time += 1
                    
                    # Recargar estado
                    if os.path.exists(conversation_file):
                        with open(conversation_file, 'r') as f:
                            state = json.load(f)
                    
                    greeting_ready = state.get('greeting_ready', False)
                    greeting_fallback = state.get('greeting_fallback', False)
                    
                    print(f"  [{wait_time}s] Listo: {greeting_ready}, Fallback: {greeting_fallback}")
                    
                    if greeting_ready or greeting_fallback:
                        break
                
                # 4. Verificar el archivo de audio
                audio_file = state.get('greeting_audio_file')
                if audio_file and os.path.exists(audio_file):
                    file_size = os.path.getsize(audio_file)
                    print(f"✅ Archivo de audio encontrado: {audio_file} ({file_size} bytes)")
                else:
                    print(f"❌ Archivo de audio no encontrado: {audio_file}")
                
                # 5. Simular llegada de llamada
                print(f"📞 Simulando llegada de llamada...")
                
                # Verificar estadísticas de audio
                stats_response = requests.get(f"{base_url}/audio-stats")
                if stats_response.status_code == 200:
                    stats = stats_response.json()
                    print(f"📊 Estadísticas de audio: {stats}")
                
            else:
                print(f"❌ No se encontró archivo de conversación: {conversation_file}")
        
        else:
            print(f"❌ Error programando llamada: {response.status_code}")
            print(f"Respuesta: {response.text}")
    
    except Exception as e:
        print(f"❌ Error en prueba: {e}")

def test_multiple_greetings():
    """Prueba generación de múltiples saludos para verificar que no se dupliquen"""
    
    base_url = "http://localhost:4000"
    
    print("\n🧪 Probando generación de múltiples saludos...")
    
    test_numbers = [
        ("+573001234568", "María García"),
        ("+573001234569", "Carlos López"),
        ("+573001234570", "Ana Rodríguez")
    ]
    
    for number, name in test_numbers:
        print(f"\n📞 Probando {name} ({number})...")
        
        try:
            # Programar llamada
            response = requests.post(f"{base_url}/schedule_call", json={
                "number": number,
                "name": name
            })
            
            if response.status_code == 200:
                print(f"✅ Llamada programada para {name}")
                
                # Esperar un poco
                time.sleep(2)
                
                # Verificar estado
                conversation_file = f"conversations/conversation-{number}.json"
                if os.path.exists(conversation_file):
                    with open(conversation_file, 'r') as f:
                        state = json.load(f)
                    
                    greeting_ready = state.get('greeting_ready', False)
                    audio_file = state.get('greeting_audio_file')
                    
                    print(f"  - Listo: {greeting_ready}")
                    print(f"  - Archivo: {audio_file}")
                    
                    if audio_file and os.path.exists(audio_file):
                        file_size = os.path.getsize(audio_file)
                        print(f"  - Tamaño: {file_size} bytes")
                    else:
                        print(f"  - ❌ Archivo no encontrado")
                else:
                    print(f"  - ❌ No se creó archivo de conversación")
            else:
                print(f"❌ Error programando llamada para {name}")
        
        except Exception as e:
            print(f"❌ Error probando {name}: {e}")

def cleanup_test_files():
    """Limpia archivos de prueba"""
    print("\n🧹 Limpiando archivos de prueba...")
    
    test_numbers = [
        "+573001234567",
        "+573001234568", 
        "+573001234569",
        "+573001234570"
    ]
    
    for number in test_numbers:
        # Limpiar archivos de conversación
        conversation_file = f"conversations/conversation-{number}.json"
        if os.path.exists(conversation_file):
            os.remove(conversation_file)
            print(f"🗑️ Eliminado: {conversation_file}")
        
        # Limpiar archivos de transcripción
        transcript_file = f"transcripts/transcript-{number}.json"
        if os.path.exists(transcript_file):
            os.remove(transcript_file)
            print(f"🗑️ Eliminado: {transcript_file}")
    
    # Limpiar archivos de audio de prueba
    audio_dir = "audio"
    if os.path.exists(audio_dir):
        for filename in os.listdir(audio_dir):
            if filename.startswith("greeting_") and any(number.replace("+", "") in filename for number in test_numbers):
                file_path = os.path.join(audio_dir, filename)
                os.remove(file_path)
                print(f"🗑️ Eliminado: {file_path}")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de sincronización de saludos...")
    print("=" * 60)
    
    try:
        # Ejecutar pruebas
        test_greeting_synchronization()
        test_multiple_greetings()
        
        print("\n" + "=" * 60)
        print("✅ Pruebas completadas")
        
        # Preguntar si limpiar archivos
        response = input("\n¿Deseas limpiar los archivos de prueba? (y/n): ")
        if response.lower() in ['y', 'yes', 'sí', 'si']:
            cleanup_test_files()
            print("✅ Limpieza completada")
        else:
            print("📁 Archivos de prueba conservados")
    
    except KeyboardInterrupt:
        print("\n⏹️ Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {e}") 