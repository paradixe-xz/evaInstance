#!/usr/bin/env python3
"""
Script de prueba para WhatsApp Business API
"""

import requests
import pandas as pd
import json
import time
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:4000"
TEST_NUMBER = "+573001234567"  # Cambiar por tu número de prueba

def test_send_whatsapp_business_message():
    """Prueba envío de mensaje individual con WhatsApp Business API"""
    print("🧪 Probando envío de mensaje WhatsApp Business...")
    
    data = {
        'to': TEST_NUMBER,
        'message': 'Hola, soy Ana de AVANZA. Esta es una prueba del sistema WhatsApp Business API. ¿Cómo estás?',
        'name': 'Usuario Prueba'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/send_whatsapp", data=data)
        result = response.json()
        
        if response.status_code == 200 and result.get('status') == 'success':
            print("✅ Mensaje enviado exitosamente")
            print(f"   Message ID: {result.get('message_id')}")
            print(f"   Provider: {result.get('provider')}")
        else:
            print("❌ Error enviando mensaje")
            print(f"   Response: {result}")
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")

def test_whatsapp_business_specific_endpoint():
    """Prueba endpoint específico de WhatsApp Business API"""
    print("\n🧪 Probando endpoint específico WhatsApp Business...")
    
    data = {
        'to': TEST_NUMBER,
        'message': 'Hola desde endpoint específico de WhatsApp Business API'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/whatsapp/business/send", data=data)
        result = response.json()
        
        if response.status_code == 200 and result.get('status') == 'success':
            print("✅ Mensaje enviado exitosamente")
            print(f"   Message ID: {result.get('message_id')}")
            print(f"   Provider: {result.get('provider')}")
        else:
            print("❌ Error enviando mensaje")
            print(f"   Response: {result}")
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")

def test_bulk_whatsapp_business_send():
    """Prueba envío masivo con WhatsApp Business API"""
    print("\n🧪 Probando envío masivo WhatsApp Business...")
    
    # Crear archivo Excel de prueba
    test_data = {
        'numero': [TEST_NUMBER, '+573007654321'],
        'mensaje': [
            'Hola, soy Ana de AVANZA. Prueba 1 del sistema masivo WhatsApp Business.',
            'Hola, soy Ana de AVANZA. Prueba 2 del sistema masivo WhatsApp Business.'
        ],
        'nombre': ['Usuario 1', 'Usuario 2']
    }
    
    df = pd.DataFrame(test_data)
    test_file = 'test_whatsapp_business_contacts.xlsx'
    df.to_excel(test_file, index=False)
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/whatsapp/bulk_send", files=files)
        
        result = response.json()
        
        if response.status_code == 200:
            print("✅ Envío masivo completado")
            print(f"   Total: {result.get('total_contacts')}")
            print(f"   Exitosos: {result.get('success_count')}")
            print(f"   Errores: {result.get('error_count')}")
        else:
            print("❌ Error en envío masivo")
            print(f"   Response: {result}")
            
    except Exception as e:
        print(f"❌ Error en prueba masiva: {e}")
    finally:
        # Limpiar archivo de prueba
        import os
        if os.path.exists(test_file):
            os.remove(test_file)

def test_whatsapp_business_info():
    """Prueba obtención de información del número de WhatsApp Business"""
    print("\n🧪 Probando información de WhatsApp Business...")
    
    try:
        response = requests.get(f"{BASE_URL}/whatsapp/business/info")
        result = response.json()
        
        if response.status_code == 200:
            if result.get('status') == 'success':
                print("✅ Información obtenida exitosamente")
                print(f"   Número: {result.get('phone_number')}")
                print(f"   Nombre verificado: {result.get('verified_name')}")
                print(f"   Calificación: {result.get('quality_rating')}")
            else:
                print("⚠️ WhatsApp Business API no configurado")
                print(f"   Error: {result.get('error')}")
        else:
            print("❌ Error obteniendo información")
            print(f"   Response: {result}")
            
    except Exception as e:
        print(f"❌ Error en prueba de información: {e}")

def test_whatsapp_business_templates():
    """Prueba obtención de plantillas de WhatsApp Business"""
    print("\n🧪 Probando plantillas de WhatsApp Business...")
    
    try:
        response = requests.get(f"{BASE_URL}/whatsapp/business/templates")
        result = response.json()
        
        if response.status_code == 200:
            if result.get('status') == 'success':
                templates = result.get('templates', [])
                print("✅ Plantillas obtenidas exitosamente")
                print(f"   Total plantillas: {len(templates)}")
                
                for template in templates[:3]:  # Mostrar solo las primeras 3
                    print(f"   - {template.get('name')}: {template.get('status')}")
            else:
                print("⚠️ WhatsApp Business API no configurado")
                print(f"   Error: {result.get('error')}")
        else:
            print("❌ Error obteniendo plantillas")
            print(f"   Response: {result}")
            
    except Exception as e:
        print(f"❌ Error en prueba de plantillas: {e}")

def test_webhook_simulation():
    """Simula un webhook de WhatsApp Business API"""
    print("\n🧪 Simulando webhook de WhatsApp Business...")
    
    # Simular datos que enviaría Meta
    webhook_data = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "1234567890",
                                "phone_number_id": "987654321"
                            },
                            "messages": [
                                {
                                    "from": TEST_NUMBER,
                                    "id": "test_message_id_123",
                                    "timestamp": str(int(time.time())),
                                    "type": "text",
                                    "text": {
                                        "body": "Hola, me interesa el préstamo"
                                    }
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/whatsapp/business/webhook", json=webhook_data)
        
        if response.status_code == 200:
            print("✅ Webhook procesado exitosamente")
            print("   (Verificar que se envió respuesta automática)")
        else:
            print("❌ Error procesando webhook")
            print(f"   Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error en simulación de webhook: {e}")

def test_server_status():
    """Prueba estado del servidor"""
    print("🧪 Verificando estado del servidor...")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        result = response.json()
        
        if response.status_code == 200:
            print("✅ Servidor funcionando correctamente")
            print(f"   Mensaje: {result.get('message')}")
        else:
            print("❌ Error en servidor")
            print(f"   Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error conectando al servidor: {e}")

def main():
    """Ejecuta todas las pruebas"""
    print("🚀 Iniciando pruebas de WhatsApp Business API")
    print("=" * 60)
    
    # Verificar que el servidor esté corriendo
    test_server_status()
    
    # Ejecutar pruebas
    test_send_whatsapp_business_message()
    test_whatsapp_business_specific_endpoint()
    test_bulk_whatsapp_business_send()
    test_whatsapp_business_info()
    test_whatsapp_business_templates()
    test_webhook_simulation()
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas")
    print("\n📋 Notas importantes:")
    print("   - Verifica que las variables de entorno estén configuradas")
    print("   - WHATSAPP_ACCESS_TOKEN debe ser válido")
    print("   - WHATSAPP_PHONE_NUMBER_ID debe estar configurado")
    print("   - Para pruebas reales, usa ngrok: ngrok http 4000")
    print("   - Configura webhook en Meta Developer Console")
    print("   - Cambia TEST_NUMBER por tu número real")

if __name__ == "__main__":
    main() 