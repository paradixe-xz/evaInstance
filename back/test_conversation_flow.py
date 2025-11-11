"""
Script para probar el flujo de conversación con integración de IA Ollama
"""
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# Asegurarse de que Python pueda encontrar los módulos de la aplicación
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar servicios reales
from app.services.conversation_service import ConversationService
from app.services.ollama_service import OllamaService
from app.config.conversation_flows import DEFAULT_ISA_FLOW

class AIConversationManager:
    """Gestiona la conversación con IA siguiendo el flujo definido"""
    
    def __init__(self):
        self.ollama = OllamaService()
        self.conversation_service = ConversationService()
        self.user_id = "test_user_123"
        self.conversation_history: List[Dict[str, str]] = []
        
        # Inicializar la conversación
        self.conversation_service.initialize_conversation(self.user_id)
        self.current_flow = DEFAULT_ISA_FLOW
        self.current_step = "initial_greeting"
    
    def get_system_prompt(self) -> str:
        """Genera el prompt del sistema basado en el paso actual"""
        step_data = self.current_flow.get(self.current_step, {})
        
        # Si estamos en modo conversación con IA
        if self.current_step == 'ai_conversation':
            prompt = """Eres ISA, una asesora de seguros profesional, amable y servicial de Seguros Mundial. 
            Estás hablando con un cliente que necesita asesoría sobre seguros. 
            
            Sigue estas reglas:
            1. Mantén un tono amable, profesional y cercano.
            2. Haz preguntas relevantes para entender las necesidades del cliente.
            3. Ofrece información general sobre los seguros disponibles.
            4. Si el cliente está interesado en un seguro específico, pide los datos necesarios.
            5. No des información financiera o legal específica, solo orientación general.
            6. Si el cliente quiere salir de la conversación, despídete amablemente.
            
            Tienes acceso a los siguientes seguros:
            - Seguro de Hogar "Vive Tranqui"
            - Seguro Oncológico "Venzamos"
            - Seguro para Mascotas "Peludito"
            """
            
            # Agregar historial de conversación relevante
            if self.conversation_history:
                prompt += "\n\nHistorial reciente de la conversación:\n"
                for msg in self.conversation_history[-5:]:  # Mostrar solo los últimos 5 mensajes
                    role = "Usuario" if msg["role"] == "user" else "Asistente"
                    prompt += f"{role}: {msg['content']}\n"
            
            return prompt
        
        # Para otros pasos del flujo
        prompt = """Eres ISA, una asesora de seguros profesional, amable y servicial. 
        Estás hablando con un cliente que necesita asesoría sobre seguros. 
        Sigue estas reglas:
        
        1. Mantén un tono amable, profesional y cercano.
        2. Haz preguntas relevantes basadas en el contexto de la conversación.
        3. No des información financiera o legal específica, solo orientación general.
        4. Si el cliente quiere salir de la conversación, despídete amablemente.
        
        Contexto actual del flujo de conversación:
        """
        
        if step_data:
            prompt += f"\n- Paso actual: {self.current_step}"
            if 'message' in step_data:
                prompt += f"\n- Objetivo del paso: {step_data['message']}"
            if 'options' in step_data:
                options = step_data['options']
                if isinstance(options, dict):
                    prompt += "\n- Opciones disponibles: " + ", ".join([f"{k}: {v}" for k, v in options.items()])
                elif isinstance(options, list):
                    prompt += "\n- Opciones disponibles: " + ", ".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
        
        return prompt
    
    def get_next_ai_response(self, user_input: str) -> str:
        """Obtiene la siguiente respuesta de la IA basada en el flujo de conversación"""
        try:
            # Obtener el paso actual del flujo
            step_data = self.current_flow.get(self.current_step, {})
            
            # Agregar el mensaje del usuario al historial si no está vacío
            if user_input and user_input.strip() and not user_input.isdigit():
                self.conversation_history.append({"role": "user", "content": user_input})
            
            # Si el usuario responde 'sí' a la autorización, ir directamente a la IA
            if self.current_step == 'data_authorization' and user_input.lower() in ('sí', 'si', 's'):
                self.current_step = 'ai_conversation'
                # Generar un mensaje de bienvenida de la IA
                system_prompt = self.get_system_prompt()
                response = self.ollama.generate_response(
                    user_message="El cliente ha aceptado los términos. Inicia la conversación de manera natural.",
                    conversation_history=self.conversation_history,
                    user_context={"system_prompt": system_prompt}
                )
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
                
            # Si el paso actual es selección de seguro, saltar a IA
            if self.current_step == 'insurance_selection':
                self.current_step = 'ai_conversation'
                system_prompt = self.get_system_prompt()
                response = self.ollama.generate_response(
                    user_message=f"El cliente seleccionó la opción {user_input}. Inicia la conversación de manera natural.",
                    conversation_history=self.conversation_history,
                    user_context={"system_prompt": system_prompt}
                )
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
            
            # Si estamos en modo conversación con IA
            if self.current_step == 'ai_conversation':
                # Si la entrada es un número, probablemente sea una selección de opción anterior
                if user_input.isdigit():
                    return "Por favor, cuéntame más sobre lo que necesitas. Estoy aquí para ayudarte con cualquier pregunta sobre nuestros seguros."
                
                # Obtener el contexto del paso actual
                system_prompt = self.get_system_prompt()
                
                # Generar respuesta usando Ollama
                response = self.ollama.generate_response(
                    user_message=user_input,
                    conversation_history=self.conversation_history,
                    user_context={"system_prompt": system_prompt}
                )
                
                # Actualizar el historial con la respuesta de la IA
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
            
            # Si hay un mensaje predefinido para este paso, usarlo
            if 'message' in step_data:
                response = step_data['message']
                
                # Si hay opciones, agregarlas al mensaje
                if 'options' in step_data and step_data['options']:
                    options = step_data['options']
                    response += "\n\nOpciones:\n"
                    if isinstance(options, dict):
                        for key, value in options.items():
                            response += f"{key}. {value}\n"
                    elif isinstance(options, list):
                        for i, option in enumerate(options, 1):
                            response += f"{i}. {option}\n"
                
                # Actualizar el siguiente paso basado en la entrada del usuario
                if 'next_step' in step_data:
                    next_step = step_data['next_step']
                    
                    # Si el siguiente paso es un diccionario, buscar la opción seleccionada
                    if isinstance(next_step, dict):
                        # Verificar si la entrada del usuario es un número que coincide con una opción
                        if 'options' in step_data and isinstance(step_data['options'], list):
                            try:
                                option_index = int(user_input.strip()) - 1
                                if 0 <= option_index < len(step_data['options']):
                                    selected_option = str(option_index + 1)
                                    if selected_option in next_step:
                                        self.current_step = next_step[selected_option]
                            except (ValueError, IndexError):
                                # Si no es un número válido, verificar si la entrada coincide con alguna clave
                                if user_input.lower() in next_step:
                                    self.current_step = next_step[user_input.lower()]
                        else:
                            # Para opciones de diccionario
                            if user_input.lower() in next_step:
                                self.current_step = next_step[user_input.lower()]
                    else:
                        # Si es un string, ir directamente a ese paso
                        self.current_step = next_step
                
                return response
            
            # Si no hay mensaje predefinido, usar la IA
            else:
                # Obtener el contexto del paso actual
                system_prompt = self.get_system_prompt()
                
                # Generar respuesta usando Ollama
                response = self.ollama.generate_response(
                    user_message=user_input,
                    conversation_history=self.conversation_history,
                    user_context={"system_prompt": system_prompt}
                )
                
                # Actualizar el historial con la respuesta de la IA
                self.conversation_history.append({"role": "assistant", "content": response})
                
                # Actualizar el siguiente paso basado en la respuesta
                self._update_conversation_flow(user_input, response)
                
                return response
            
        except Exception as e:
            error_msg = f"Lo siento, estoy teniendo problemas para procesar tu solicitud. Error: {str(e)}"
            self.conversation_history.append({"role": "assistant", "content": error_msg})
            return error_msg
    
    def _update_conversation_flow(self, user_input: str, ai_response: str):
        """Actualiza el flujo de la conversación basado en la interacción actual"""
        # No actualizar el flujo si estamos en modo conversación con IA
        if self.current_step == 'ai_conversation':
            return
            
        step_data = self.current_flow.get(self.current_step, {})
        
        # Si no hay un siguiente paso definido, mantener el paso actual
        if 'next_step' not in step_data:
            return
            
        next_step = step_data['next_step']
        
        # Si el siguiente paso es un diccionario, depende de la entrada del usuario
        if isinstance(next_step, dict):
            # Verificar si la entrada del usuario coincide con alguna opción
            if 'options' in step_data and isinstance(step_data['options'], list):
                try:
                    option_index = int(user_input.strip()) - 1
                    if 0 <= option_index < len(step_data['options']):
                        selected_option = str(option_index + 1)
                        if selected_option in next_step:
                            self.current_step = next_step[selected_option]
                except (ValueError, IndexError):
                    # Si no es un número válido, verificar si la entrada coincide con alguna clave
                    if user_input.lower() in next_step:
                        self.current_step = next_step[user_input.lower()]
            else:
                # Para opciones de diccionario
                if user_input.lower() in next_step:
                    self.current_step = next_step[user_input.lower()]
        else:
            # Si es un string, ir directamente a ese paso
            self.current_step = next_step
        
        # Guardar datos relevantes del usuario
        self._save_user_data(user_input)
    
    def _save_user_data(self, user_input: str):
        """Guarda datos relevantes del usuario según el paso actual"""
        if not user_input or not user_input.strip():
            return
            
        step_data = self.current_flow.get(self.current_step, {})
        
        # Inicializar datos del usuario si no existen
        if not hasattr(self.conversation_service, 'conversation_states'):
            self.conversation_service.conversation_states = {}
            
        if self.user_id not in self.conversation_service.conversation_states:
            self.conversation_service.conversation_states[self.user_id] = {
                'data': {},
                'current_step': self.current_step,
                'history': []
            }
        
        # Guardar el paso actual
        self.conversation_service.conversation_states[self.user_id]['current_step'] = self.current_step
        
        # Guardar datos específicos del paso actual
        if 'field' in step_data:
            field_name = step_data['field']
            self.conversation_service.conversation_states[self.user_id]['data'][field_name] = user_input
        
        # Guardar respuestas a preguntas específicas
        if 'questions' in step_data and isinstance(step_data['questions'], list):
            for question in step_data['questions']:
                if isinstance(question, dict) and 'question' in question and 'field' in question:
                    if question['question'] in user_input:
                        # Extraer la respuesta del usuario
                        answer = user_input.replace(question['question'], '').strip()
                        if answer:
                            self.conversation_service.conversation_states[self.user_id]['data'][question['field']] = answer
        
        # Guardar el historial de la conversación
        if len(self.conversation_history) > 0:
            last_message = self.conversation_history[-1]
            if last_message['role'] == 'user' and last_message['content'] == user_input:
                self.conversation_service.conversation_states[self.user_id]['history'].append({
                    'step': self.current_step,
                    'user_input': user_input,
                    'timestamp': datetime.now().isoformat()
                })

class ConversationTester:
    """Clase para probar el flujo de conversación con IA"""
    
    def __init__(self):
        self.ai_manager = AIConversationManager()
        self.user_id = "test_user_123"
        self.running = True
    
    def clear_screen(self):
        """Limpia la pantalla de la consola"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Muestra el encabezado de la aplicación"""
        print("🤖 ISA - Asistente de Seguros con IA")
        print("=" * 80)
        print("Este es un asistente virtual que te ayudará con información sobre seguros.")
        print("Puedes hablar con naturalidad y hacer las preguntas que necesites.")
        print("\nComandos especiales:")
        print("  - 'salir': Terminar la conversación")
        print("  - 'reiniciar': Comenzar una nueva conversación")
        print("  - 'estado': Ver el estado actual de la conversación")
        print("-" * 80 + "\n")
    
    def print_response(self, response: str):
        """Muestra la respuesta del asistente"""
        # Limpiar la respuesta de caracteres especiales que puedan causar problemas
        response = response.replace('\x1b[0m', '').replace('\x1b[1m', '')
        print(f"\n🤖 ISA: {response}\n")
    
    def handle_special_commands(self, user_input: str) -> bool:
        """Maneja los comandos especiales y devuelve True si se manejó un comando"""
        user_input = user_input.lower().strip()
        
        if user_input in ('salir', 'exit', 'q'):
            print("\n👋 ¡Hasta luego! Ha sido un placer ayudarte.")
            self.running = False
            return True
            
        if user_input == 'reiniciar':
            self.ai_manager = AIConversationManager()
            print("\n🔄 Conversación reiniciada\n")
            welcome_msg = self.ai_manager.get_next_ai_response("")
            self.print_response(welcome_msg)
            return True
            
        if user_input == 'estado':
            print("\n📋 ESTADO ACTUAL:")
            print(f"Paso actual: {self.ai_manager.current_step}")
            print(f"Historial de la conversación: {len(self.ai_manager.conversation_history)} mensajes")
            
            # Mostrar datos guardados del usuario si existen
            if hasattr(self.ai_manager.conversation_service, 'conversation_states'):
                user_data = self.ai_manager.conversation_service.conversation_states.get(self.user_id, {})
                if user_data:
                    print("\n📂 Datos del usuario:")
                    for key, value in user_data.get('data', {}).items():
                        print(f"- {key}: {value}")
            
            print()
            return True
            
        return False
    
    def run(self):
        """Ejecuta el bucle principal de la conversación"""
        self.clear_screen()
        self.print_header()
        
        # Obtener el mensaje de bienvenida
        welcome_msg = self.ai_manager.get_next_ai_response("")
        self.print_response(welcome_msg)
        
        while self.running:
            try:
                # Obtener entrada del usuario
                user_input = input("TÚ: ").strip()
                
                # Manejar comandos especiales
                if self.handle_special_commands(user_input):
                    continue
                
                # Procesar el mensaje del usuario
                response = self.ai_manager.get_next_ai_response(user_input)
                self.print_response(response)
                
                # Verificar si la conversación ha terminado
                if self.ai_manager.current_step == 'end_conversation':
                    print("\n🔚 La conversación ha terminado. Escribe 'reiniciar' para comenzar de nuevo o 'salir' para terminar.")
                
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
                print("\n🔄 Continuando con la conversación...\n")
                continue

if __name__ == "__main__":
    import json
    tester = ConversationTester()
    tester.run()  # Ejecutar de manera síncrona
