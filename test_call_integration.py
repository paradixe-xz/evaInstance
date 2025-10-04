"""
Pruebas de integración para el sistema de llamadas
"""
import pytest
import requests
import time
from unittest.mock import patch, MagicMock

# Configuración de pruebas
BASE_URL = "http://localhost:8000"
CALL_API_URL = f"{BASE_URL}/api/v1/calls"

class TestCallIntegration:
    """Pruebas de integración para llamadas telefónicas"""
    
    def test_health_check(self):
        """Verificar que el endpoint de salud funciona"""
        response = requests.get(f"{CALL_API_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_kanitts_service_availability(self):
        """Verificar disponibilidad del servicio KaniTTS"""
        response = requests.get(f"{CALL_API_URL}/health")
        assert response.status_code == 200
        data = response.json()
        # KaniTTS puede estar disponible o no, pero el endpoint debe responder
        assert "kanitts" in data
    
    @patch('app.services.call_service.Client')
    def test_make_outgoing_call(self, mock_twilio_client):
        """Probar llamada saliente"""
        # Mock de Twilio
        mock_call = MagicMock()
        mock_call.sid = "test_call_sid_123"
        mock_twilio_client.return_value.calls.create.return_value = mock_call
        
        # Datos de prueba
        call_data = {
            "to_number": "+1234567890",
            "message": "Hola, esta es una prueba de llamada."
        }
        
        response = requests.post(f"{CALL_API_URL}/make-call", json=call_data)
        assert response.status_code == 200
        data = response.json()
        assert "call_sid" in data
        assert data["call_sid"] == "test_call_sid_123"
    
    def test_incoming_call_webhook(self):
        """Probar webhook de llamada entrante"""
        # Simular datos de webhook de Twilio
        webhook_data = {
            "CallSid": "test_incoming_call_123",
            "From": "+1234567890",
            "To": "+0987654321",
            "CallStatus": "ringing"
        }
        
        response = requests.post(
            f"{CALL_API_URL}/webhook/incoming",
            data=webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        # Verificar que la respuesta contiene TwiML válido
        assert "<?xml version=" in response.text
        assert "<Response>" in response.text
    
    def test_speech_processing_webhook(self):
        """Probar procesamiento de voz en webhook"""
        # Simular datos de webhook con transcripción
        webhook_data = {
            "CallSid": "test_speech_call_123",
            "SpeechResult": "Hola, quiero información sobre sus servicios",
            "Confidence": "0.95"
        }
        
        response = requests.post(
            f"{CALL_API_URL}/webhook/speech",
            data=webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        # Verificar que la respuesta contiene TwiML válido
        assert "<?xml version=" in response.text
        assert "<Response>" in response.text
    
    def test_start_conversation(self):
        """Probar inicio de conversación"""
        conversation_data = {
            "phone_number": "+1234567890",
            "initial_message": "Hola, ¿cómo estás?"
        }
        
        response = requests.post(
            f"{CALL_API_URL}/conversation/start",
            json=conversation_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert "status" in data
        assert data["status"] == "started"
    
    def test_get_conversation_history(self):
        """Probar obtención de historial de conversación"""
        # Primero iniciar una conversación
        conversation_data = {
            "phone_number": "+1234567890",
            "initial_message": "Prueba de historial"
        }
        
        start_response = requests.post(
            f"{CALL_API_URL}/conversation/start",
            json=conversation_data
        )
        
        assert start_response.status_code == 200
        conversation_id = start_response.json()["conversation_id"]
        
        # Obtener historial
        history_response = requests.get(
            f"{CALL_API_URL}/conversation/{conversation_id}/history"
        )
        
        assert history_response.status_code == 200
        data = history_response.json()
        assert "conversation_id" in data
        assert "messages" in data
        assert isinstance(data["messages"], list)
    
    def test_end_conversation(self):
        """Probar finalización de conversación"""
        # Primero iniciar una conversación
        conversation_data = {
            "phone_number": "+1234567890",
            "initial_message": "Prueba de finalización"
        }
        
        start_response = requests.post(
            f"{CALL_API_URL}/conversation/start",
            json=conversation_data
        )
        
        assert start_response.status_code == 200
        conversation_id = start_response.json()["conversation_id"]
        
        # Finalizar conversación
        end_response = requests.post(
            f"{CALL_API_URL}/conversation/{conversation_id}/end"
        )
        
        assert end_response.status_code == 200
        data = end_response.json()
        assert "status" in data
        assert data["status"] == "ended"

if __name__ == "__main__":
    # Ejecutar pruebas básicas
    print("🧪 Ejecutando pruebas de integración de llamadas...")
    
    try:
        # Verificar que el servidor esté ejecutándose
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ El servidor no está ejecutándose en http://localhost:8000")
            exit(1)
        
        print("✅ Servidor disponible")
        
        # Ejecutar pruebas básicas
        test_instance = TestCallIntegration()
        
        print("🔍 Probando health check...")
        test_instance.test_health_check()
        print("✅ Health check OK")
        
        print("🔍 Probando webhook de llamada entrante...")
        test_instance.test_incoming_call_webhook()
        print("✅ Webhook entrante OK")
        
        print("🔍 Probando inicio de conversación...")
        test_instance.test_start_conversation()
        print("✅ Inicio de conversación OK")
        
        print("\n🎉 Todas las pruebas básicas pasaron exitosamente!")
        print("💡 Para ejecutar todas las pruebas: pytest test_call_integration.py -v")
        
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor. Asegúrate de que esté ejecutándose:")
        print("   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")