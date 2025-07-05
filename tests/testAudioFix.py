#!/usr/bin/env python3
"""
Script de prueba para verificar la corrección del audio
"""

import requests
import time
import json
import os

# Configuración
BASE_URL = "http://localhost:4000"

def test_audio_generation():
    """Prueba la generación de audio"""
    print("\n🎵 Probando generación de audio...")
    
    start_time = time.time()
    
    response = requests.get(f"{BASE_URL}/test-tts")
    
    end_time = time.time()
    generation_time = end_time - start_time
    
    if response.status_code == 200:
        result = response.json()
        if result.get('status') == 'success':
            print(f"✅ Audio generado en {generation_time:.2f} segundos")
            print(f"   Archivo: {result.get('file', 'N/A')}")
            print(f"   URL: {result.get('url', 'N/A')}")
            
            # Verificar que el archivo existe
            file_path = result.get('file', '')
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"   Tamaño: {file_size} bytes")
                
                if file_size > 1000:  # Más de 1KB
                    print("   ✅ Archivo de audio válido")
                else:
                    print("   ⚠️ Archivo muy pequeño, puede estar corrupto")
            else:
                print("   ❌ Archivo no encontrado")
            
            return True
        else:
            print(f"❌ Error en TTS: {result.get('message', 'N/A')}")
            return False
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return False

def test_audio_stats():
    """Prueba las estadísticas de audio"""
    print("\n📊 Probando estadísticas de audio...")
    
    response = requests.get(f"{BASE_URL}/audio-stats")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Estadísticas de audio:")
        print(f"   Archivos totales: {stats.get('total_files', 0)}")
        print(f"   Tamaño total: {stats.get('total_size', '0 MB')}")
        print(f"   Colas activas: {stats.get('active_queues', 0)}")
        return stats
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None

def test_cleanup_audio():
    """Prueba la limpieza de audio"""
    print("\n🧹 Probando limpieza de audio...")
    
    response = requests.post(f"{BASE_URL}/cleanup-audio")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('status') == 'success':
            print(f"✅ Limpieza completada: {result.get('message', '')}")
            return True
        else:
            print(f"❌ Error en limpieza: {result.get('message', '')}")
            return False
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return False

def test_server_status():
    """Prueba el estado del servidor"""
    print("\n🌐 Probando estado del servidor...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor funcionando correctamente")
            return True
        else:
            print(f"❌ Servidor respondió con código: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout conectando al servidor")
        return False

def main():
    """Función principal de pruebas"""
    print("🔧 Iniciando pruebas de corrección de audio")
    print("=" * 50)
    
    # Verificar que el servidor esté corriendo
    if not test_server_status():
        print("\n❌ Servidor no disponible. Asegúrate de que esté corriendo con:")
        print("   ./scripts/runServer.sh")
        return
    
    # Ejecutar pruebas
    tests = [
        ("Estado del servidor", test_server_status),
        ("Generación de audio", test_audio_generation),
        ("Estadísticas de audio", test_audio_stats),
        ("Limpieza de audio", test_cleanup_audio),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Error en prueba '{test_name}': {e}")
            results[test_name] = False
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS DE AUDIO")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"✅ Pruebas pasadas: {passed}/{total}")
    
    if results.get("Generación de audio"):
        print("✅ Audio generado correctamente")
    else:
        print("❌ Problemas con generación de audio")
    
    if results.get("Estadísticas de audio"):
        print("✅ Estadísticas funcionando")
    else:
        print("❌ Problemas con estadísticas")
    
    if results.get("Limpieza de audio"):
        print("✅ Limpieza funcionando")
    else:
        print("❌ Problemas con limpieza")
    
    print("\n🎯 Correcciones implementadas:")
    print("   • Detección automática de formato de audio")
    print("   • Fallback con ffmpeg directo")
    print("   • Manejo robusto de errores")
    print("   • Timeout aumentado para generación")
    print("   • Archivos de audio de fallback")
    
    if passed == total:
        print("\n🎉 ¡Todas las pruebas pasaron! El audio debería funcionar correctamente.")
    else:
        print(f"\n⚠️ {total - passed} pruebas fallaron. Revisa los logs para más detalles.")

if __name__ == "__main__":
    main() 