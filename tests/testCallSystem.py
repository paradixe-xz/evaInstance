#!/usr/bin/env python3
"""
Script de prueba para el sistema de llamadas directas con transcripción y análisis de IA
"""

import requests
import json
import pandas as pd
from datetime import datetime
import os

# Configuración
BASE_URL = "http://localhost:8000"
TEST_FILE = "test_contacts.xlsx"

def create_test_contacts():
    """Crea un archivo Excel de prueba con contactos"""
    test_data = {
        'nombre': [
            'Juan Pérez',
            'María García', 
            'Carlos López',
            'Ana Martínez',
            'Roberto Silva'
        ],
        'numero': [
            '+573001234567',
            '+573001234568',
            '+573001234569', 
            '+573001234570',
            '+573001234571'
        ]
    }
    
    df = pd.DataFrame(test_data)
    df.to_excel(TEST_FILE, index=False)
    print(f"✅ Archivo de prueba creado: {TEST_FILE}")
    return TEST_FILE

def test_upload_contacts():
    """Prueba la subida de contactos y programación de llamadas"""
    print("\n🔄 Probando subida de contactos...")
    
    if not os.path.exists(TEST_FILE):
        create_test_contacts()
    
    with open(TEST_FILE, 'rb') as f:
        files = {'file': (TEST_FILE, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(f"{BASE_URL}/sendNumbers", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Contactos procesados: {result.get('valid_contacts', 0)} válidos")
        print(f"📊 Total: {result.get('total_contacts', 0)}")
        print(f"❌ Inválidos: {result.get('invalid_contacts', 0)}")
        return result
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None

def test_conversations_status():
    """Prueba el endpoint de estado de conversaciones"""
    print("\n🔄 Probando estado de conversaciones...")
    
    response = requests.get(f"{BASE_URL}/conversations/status")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Conversaciones activas: {result.get('total_conversations', 0)}")
        
        conversations = result.get('conversations', [])
        for conv in conversations[:3]:  # Mostrar solo las primeras 3
            print(f"   📞 {conv.get('number', 'N/A')} - {conv.get('name', 'N/A')}")
            print(f"      Estado: {conv.get('stage', 'N/A')}")
            print(f"      Duración: {conv.get('call_duration', 0)}s")
        
        return result
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None

def test_ready_for_human():
    """Prueba el endpoint de conversaciones listas para seguimiento humano"""
    print("\n🔄 Probando conversaciones listas para humano...")
    
    response = requests.get(f"{BASE_URL}/analysis/ready_for_human")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Conversaciones listas: {result.get('total_ready', 0)}")
        
        conversations = result.get('conversations', [])
        for conv in conversations:
            print(f"   📞 {conv.get('number', 'N/A')} - {conv.get('name', 'N/A')}")
            analysis = conv.get('ai_analysis', {})
            print(f"      Interés: {analysis.get('interest_level', 'N/A')}")
            print(f"      Prioridad: {analysis.get('priority', 'N/A')}")
            print(f"      Duración: {conv.get('call_duration', 0)}s")
        
        return result
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None

def test_mark_closed():
    """Prueba marcar una conversación como cerrada"""
    print("\n🔄 Probando marcar conversación como cerrada...")
    
    # Primero obtener conversaciones activas
    status_response = requests.get(f"{BASE_URL}/conversations/status")
    if status_response.status_code == 200:
        conversations = status_response.json().get('conversations', [])
        
        if conversations:
            # Tomar la primera conversación
            first_conv = conversations[0]
            number = first_conv.get('number')
            
            # Marcar como cerrada
            data = {
                "number": number,
                "outcome": "interested",
                "notes": "Cliente mostró interés, necesita seguimiento"
            }
            
            response = requests.post(f"{BASE_URL}/analysis/mark_closed", json=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Conversación {number} marcada como cerrada")
                print(f"   Resultado: {result.get('outcome', 'N/A')}")
                return result
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
        else:
            print("ℹ️ No hay conversaciones activas para cerrar")
    
    return None

def test_tts():
    """Prueba el sistema de TTS"""
    print("\n🔄 Probando sistema TTS...")
    
    response = requests.get(f"{BASE_URL}/test-tts")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('status') == 'success':
            print(f"✅ TTS funcionando correctamente")
            print(f"   Archivo: {result.get('file', 'N/A')}")
            print(f"   URL: {result.get('url', 'N/A')}")
        else:
            print(f"❌ Error en TTS: {result.get('message', 'N/A')}")
        return result
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas del sistema de llamadas directas")
    print("=" * 60)
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print(f"❌ Servidor no disponible en {BASE_URL}")
            print("   Asegúrate de que el servidor esté corriendo con: python main.py")
            return
        print(f"✅ Servidor disponible en {BASE_URL}")
    except requests.exceptions.ConnectionError:
        print(f"❌ No se puede conectar al servidor en {BASE_URL}")
        print("   Asegúrate de que el servidor esté corriendo con: python main.py")
        return
    
    # Ejecutar pruebas
    tests = [
        ("TTS", test_tts),
        ("Subida de contactos", test_upload_contacts),
        ("Estado de conversaciones", test_conversations_status),
        ("Conversaciones listas para humano", test_ready_for_human),
        ("Marcar como cerrada", test_mark_closed),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Error en prueba '{test_name}': {e}")
            results[test_name] = None
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASÓ" if result is not None else "❌ FALLÓ"
        print(f"{test_name}: {status}")
        if result is not None:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El sistema está funcionando correctamente.")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los errores arriba.")
    
    # Limpiar archivo de prueba
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)
        print(f"🧹 Archivo de prueba eliminado: {TEST_FILE}")

if __name__ == "__main__":
    main() 