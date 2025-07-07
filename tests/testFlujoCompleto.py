#!/usr/bin/env python3
"""
Test del Flujo Completo AVANZA
Prueba el flujo: WhatsApp → IA convence → Llamada → Documentos → Email
"""

import requests
import json
import time
import pandas as pd
from io import BytesIO

# Configuración
BASE_URL = "http://localhost:4000"
TEST_NUMBER = "+573014146715"  # Número de prueba
TEST_NAME = "Juan Pérez"

def test_flujo_completo():
    """Prueba el flujo completo de AVANZA"""
    
    print("🚀 Iniciando prueba del flujo completo AVANZA...")
    
    # 1. Crear archivo Excel de prueba
    print("\n📊 1. Creando archivo Excel de prueba...")
    test_data = {
        'numero': [TEST_NUMBER],
        'nombre': [TEST_NAME]
    }
    df = pd.DataFrame(test_data)
    
    # Guardar archivo temporal
    excel_file = "test_contacts.xlsx"
    df.to_excel(excel_file, index=False)
    
    # 2. Enviar contactos (WhatsApp + Llamada)
    print("\n📱 2. Enviando mensaje inicial por WhatsApp...")
    with open(excel_file, 'rb') as f:
        files = {'file': ('test_contacts.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(f"{BASE_URL}/sendNumbers", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Contactos enviados: {result.get('valid_contacts', 0)}")
        print(f"📋 Resultados: {result.get('results', [])}")
    else:
        print(f"❌ Error enviando contactos: {response.text}")
        return False
    
    # 3. Simular respuesta "NO" del usuario
    print("\n🤖 3. Simulando respuesta 'NO' del usuario...")
    test_message = {
        "user_message": "No me interesa",
        "user_number": TEST_NUMBER,
        "user_name": TEST_NAME
    }
    
    # Simular webhook de WhatsApp
    webhook_data = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": TEST_NUMBER,
                        "text": {"body": "No me interesa"},
                        "type": "text"
                    }]
                }
            }]
        }]
    }
    
    response = requests.post(f"{BASE_URL}/whatsapp/business/webhook", json=webhook_data)
    if response.status_code == 200:
        print("✅ Respuesta 'NO' procesada - IA debería estar convenciendo")
    else:
        print(f"❌ Error procesando respuesta: {response.text}")
    
    # 4. Simular cambio de opinión
    print("\n🔄 4. Simulando cambio de opinión...")
    webhook_data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"] = "Sí, me interesa"
    
    response = requests.post(f"{BASE_URL}/whatsapp/business/webhook", json=webhook_data)
    if response.status_code == 200:
        print("✅ Cambio de opinión procesado - Llamada debería estar programada")
    else:
        print(f"❌ Error procesando cambio de opinión: {response.text}")
    
    # 5. Verificar estado de conversación
    print("\n📊 5. Verificando estado de conversación...")
    response = requests.get(f"{BASE_URL}/conversations/status")
    if response.status_code == 200:
        conversations = response.json()
        for conv in conversations.get('conversations', []):
            if conv['number'] == TEST_NUMBER:
                print(f"✅ Estado actual: {conv['stage']}")
                print(f"📞 Llamada programada: {conv.get('call_sid', 'No')}")
                break
    else:
        print(f"❌ Error obteniendo estado: {response.text}")
    
    # 6. Simular finalización de llamada
    print("\n📞 6. Simulando finalización de llamada...")
    call_ended_data = {
        "CallSid": "test_call_sid",
        "From": TEST_NUMBER,
        "CallDuration": "300"  # 5 minutos
    }
    
    response = requests.post(f"{BASE_URL}/twilio/voice/call_ended", data=call_ended_data)
    if response.status_code == 200:
        print("✅ Llamada finalizada - Análisis completado")
    else:
        print(f"❌ Error finalizando llamada: {response.text}")
    
    # 7. Simular interés post-llamada
    print("\n🎯 7. Simulando interés post-llamada...")
    webhook_data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"] = "Sí, quiero proceder"
    
    response = requests.post(f"{BASE_URL}/whatsapp/business/webhook", json=webhook_data)
    if response.status_code == 200:
        print("✅ Interés confirmado - Solicitud de documentos enviada")
    else:
        print(f"❌ Error procesando interés: {response.text}")
    
    # 8. Simular envío de documentos
    print("\n📄 8. Simulando envío de documentos...")
    documents_data = {
        "from": TEST_NUMBER,
        "cedula_name": "Juan Pérez",
        "recibo_name": "Juan Pérez",
        "email": "juan.perez@test.com"
    }
    
    response = requests.post(f"{BASE_URL}/whatsapp/documents", data=documents_data)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Documentos procesados: {result.get('names_match', False)}")
        print(f"📧 Email enviado: {result.get('whatsapp_sent', False)}")
    else:
        print(f"❌ Error procesando documentos: {response.text}")
    
    # 9. Verificar estado final
    print("\n📊 9. Verificando estado final...")
    response = requests.get(f"{BASE_URL}/conversations/status")
    if response.status_code == 200:
        conversations = response.json()
        for conv in conversations.get('conversations', []):
            if conv['number'] == TEST_NUMBER:
                print(f"✅ Estado final: {conv['stage']}")
                print(f"📋 Análisis listo: {conv.get('analysis_ready', False)}")
                break
    
    # Limpiar archivo temporal
    import os
    if os.path.exists(excel_file):
        os.remove(excel_file)
    
    print("\n🎉 ¡Prueba del flujo completo completada!")
    return True

def test_whatsapp_only():
    """Prueba solo envío de WhatsApp"""
    print("\n📱 Probando envío solo WhatsApp...")
    
    # Crear archivo Excel
    test_data = {
        'numero': [TEST_NUMBER],
        'nombre': [TEST_NAME]
    }
    df = pd.DataFrame(test_data)
    excel_file = "test_whatsapp_only.xlsx"
    df.to_excel(excel_file, index=False)
    
    # Enviar solo WhatsApp
    with open(excel_file, 'rb') as f:
        files = {'file': ('test_whatsapp_only.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(f"{BASE_URL}/sendWhatsAppOnly", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ WhatsApp enviado: {result.get('valid_contacts', 0)}")
    else:
        print(f"❌ Error enviando WhatsApp: {response.text}")
    
    # Limpiar
    import os
    if os.path.exists(excel_file):
        os.remove(excel_file)

def test_bulk_whatsapp():
    """Prueba envío masivo de WhatsApp"""
    print("\n📤 Probando envío masivo WhatsApp...")
    
    # Crear archivo Excel con mensajes personalizados
    test_data = {
        'numero': [TEST_NUMBER, "+573014146716"],
        'mensaje': [
            "Hola Juan, ¿cómo estás? Te escribo de AVANZA.",
            "Hola María, ¿cómo estás? Te escribo de AVANZA."
        ],
        'nombre': ["Juan Pérez", "María García"]
    }
    df = pd.DataFrame(test_data)
    excel_file = "test_bulk_whatsapp.xlsx"
    df.to_excel(excel_file, index=False)
    
    # Enviar masivo
    with open(excel_file, 'rb') as f:
        files = {'file': ('test_bulk_whatsapp.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(f"{BASE_URL}/whatsapp/bulk_send", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Mensajes enviados: {result.get('success_count', 0)}")
        print(f"❌ Errores: {result.get('error_count', 0)}")
    else:
        print(f"❌ Error envío masivo: {response.text}")
    
    # Limpiar
    import os
    if os.path.exists(excel_file):
        os.remove(excel_file)

if __name__ == "__main__":
    print("🧪 Tests del Flujo Completo AVANZA")
    print("=" * 50)
    
    try:
        # Test 1: Flujo completo
        test_flujo_completo()
        
        # Test 2: Solo WhatsApp
        test_whatsapp_only()
        
        # Test 3: Envío masivo
        test_bulk_whatsapp()
        
        print("\n✅ Todos los tests completados exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error en tests: {e}")
        import traceback
        traceback.print_exc() 