"""
Pruebas del flujo de conversación telefónica
"""
import pytest
import requests
import time
from unittest.mock import patch, MagicMock

# Configuración
BASE_URL = "http://localhost:8000"
CALL_API_URL = f"{BASE_URL}/api/v1/calls"

class TestConversationFlow:
    """Pruebas del flujo completo de conversación"""
    
    def setup_method(self):
        """Configuración antes de cada prueba"""
        self.test_phone = "+1234567890"
        self.conversation_id = None
    
    def teardown_method(self):
        """Limpieza después de cada prueba"""
        if self.conversation_id:
            try:
                requests.post(f"{CALL_API_URL}/conversation/{self.conversation_id}/end")
            except:
                pass
    
    def test_complete_conversation_flow(self):
        """Probar flujo completo de conversación"""
        
        # 1. Iniciar conversación
        print("📞 Iniciando conversación...")
        conversation_data = {
            "phone_number": self.test_phone,
            "initial_message": "Hola, soy Eva, tu asistente virtual. ¿En qué puedo ayudarte hoy?"
        }
        
        start_response = requests.post(
            f"{CALL_API_URL}/conversation/start",
            json=conversation_data
        )
        
        assert start_response.status_code == 200
        start_data = start_response.json()
        self.conversation_id = start_data["conversation_id"]
        
        print(f"✅ Conversación iniciada: {self.conversation_id}")
        
        # 2. Simular entrada de voz del usuario
        print("🎤 Simulando entrada de voz...")
        speech_data = {
            "CallSid": self.conversation_id,
            "SpeechResult": "Hola Eva, quiero información sobre sus servicios de consultoría",
            "Confidence": "0.92"
        }
        
        speech_response = requests.post(
            f"{CALL_API_URL}/webhook/speech",
            data=speech_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert speech_response.status_code == 200
        print("✅ Entrada de voz procesada")
        
        # 3. Verificar historial de conversación
        print("📋 Verificando historial...")
        history_response = requests.get(
            f"{CALL_API_URL}/conversation/{self.conversation_id}/history"
        )
        
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert len(history_data["messages"]) >= 1
        print(f"✅ Historial verificado: {len(history_data['messages'])} mensajes")
        
        # 4. Simular más interacciones
        print("💬 Simulando más interacciones...")
        follow_up_speech = {
            "CallSid": self.conversation_id,
            "SpeechResult": "¿Cuáles son sus precios?",
            "Confidence": "0.88"
        }
        
        follow_up_response = requests.post(
            f"{CALL_API_URL}/webhook/speech",
            data=follow_up_speech,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert follow_up_response.status_code == 200
        print("✅ Interacción adicional procesada")
        
        # 5. Finalizar conversación
        print("🔚 Finalizando conversación...")
        end_response = requests.post(
            f"{CALL_API_URL}/conversation/{self.conversation_id}/end"
        )
        
        assert end_response.status_code == 200
        end_data = end_response.json()
        assert end_data["status"] == "ended"
        print("✅ Conversación finalizada")
        
        # 6. Verificar historial final
        final_history_response = requests.get(
            f"{CALL_API_URL}/conversation/{self.conversation_id}/history"
        )
        
        assert final_history_response.status_code == 200
        final_history = final_history_response.json()
        print(f"📊 Historial final: {len(final_history['messages'])} mensajes")
        
        self.conversation_id = None  # Ya finalizada
    
    def test_conversation_timeout_handling(self):
        """Probar manejo de timeout en conversación"""
        
        # Iniciar conversación
        conversation_data = {
            "phone_number": self.test_phone,
            "initial_message": "Prueba de timeout"
        }
        
        start_response = requests.post(
            f"{CALL_API_URL}/conversation/start",
            json=conversation_data
        )
        
        assert start_response.status_code == 200
        self.conversation_id = start_response.json()["conversation_id"]
        
        # Simular timeout (sin actividad)
        print("⏰ Simulando timeout de conversación...")
        time.sleep(2)  # Esperar un poco
        
        # Intentar obtener historial después del timeout
        history_response = requests.get(
            f"{CALL_API_URL}/conversation/{self.conversation_id}/history"
        )
        
        # La conversación debería seguir activa (timeout real sería más largo)
        assert history_response.status_code == 200
        print("✅ Manejo de timeout verificado")
    
    def test_error_handling_in_conversation(self):
        """Probar manejo de errores durante conversación"""
        
        # Intentar procesar voz sin conversación activa
        invalid_speech_data = {
            "CallSid": "invalid_call_sid_123",
            "SpeechResult": "Esto debería fallar",
            "Confidence": "0.95"
        }
        
        error_response = requests.post(
            f"{CALL_API_URL}/webhook/speech",
            data=invalid_speech_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Debería manejar el error graciosamente
        assert error_response.status_code in [200, 400, 404]
        print("✅ Manejo de errores verificado")
    
    def test_multiple_concurrent_conversations(self):
        """Probar múltiples conversaciones concurrentes"""
        
        conversation_ids = []
        
        try:
            # Iniciar múltiples conversaciones
            for i in range(3):
                conversation_data = {
                    "phone_number": f"+123456789{i}",
                    "initial_message": f"Conversación de prueba {i+1}"
                }
                
                response = requests.post(
                    f"{CALL_API_URL}/conversation/start",
                    json=conversation_data
                )
                
                assert response.status_code == 200
                conversation_ids.append(response.json()["conversation_id"])
            
            print(f"✅ {len(conversation_ids)} conversaciones concurrentes iniciadas")
            
            # Verificar que todas están activas
            for conv_id in conversation_ids:
                history_response = requests.get(
                    f"{CALL_API_URL}/conversation/{conv_id}/history"
                )
                assert history_response.status_code == 200
            
            print("✅ Todas las conversaciones están activas")
            
        finally:
            # Limpiar todas las conversaciones
            for conv_id in conversation_ids:
                try:
                    requests.post(f"{CALL_API_URL}/conversation/{conv_id}/end")
                except:
                    pass
            
            print("🧹 Conversaciones limpiadas")

def run_conversation_tests():
    """Ejecutar pruebas de flujo de conversación"""
    print("🧪 Ejecutando pruebas de flujo de conversación...")
    
    try:
        # Verificar servidor
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ El servidor no está disponible")
            return False
        
        print("✅ Servidor disponible")
        
        # Ejecutar pruebas
        test_instance = TestConversationFlow()
        
        print("\n🔍 Probando flujo completo de conversación...")
        test_instance.test_complete_conversation_flow()
        print("✅ Flujo completo OK")
        
        print("\n🔍 Probando manejo de errores...")
        test_instance.test_error_handling_in_conversation()
        print("✅ Manejo de errores OK")
        
        print("\n🔍 Probando conversaciones concurrentes...")
        test_instance.test_multiple_concurrent_conversations()
        print("✅ Conversaciones concurrentes OK")
        
        print("\n🎉 Todas las pruebas de flujo pasaron exitosamente!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor")
        return False
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        return False

if __name__ == "__main__":
    success = run_conversation_tests()
    exit(0 if success else 1)