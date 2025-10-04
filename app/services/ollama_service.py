"""
Ollama AI service for generating responses
"""

import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.exceptions import OllamaError, ServiceUnavailableError

logger = get_logger(__name__)
settings = get_settings()


class OllamaService:
    """Service for Ollama AI operations"""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.system_prompt = settings.ollama_system_prompt
        self.max_tokens = settings.ollama_max_tokens
        self.temperature = settings.ollama_temperature
        self.timeout = settings.ollama_timeout
        
        logger.info(f"Ollama service initialized with model: {self.model}")
    
    def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate AI response using Ollama
        
        Args:
            user_message: User's message
            conversation_history: Previous conversation messages
            user_context: Additional user context (name, preferences, etc.)
            
        Returns:
            AI generated response
        """
        try:
            # Build conversation context
            messages = self._build_conversation_context(
                user_message, conversation_history, user_context
            )
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            logger.info(f"Generating response for user message: {user_message[:100]}...")
            
            # Make request to Ollama
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise OllamaError(error_msg, error_code="API_ERROR")
            
            result = response.json()
            ai_response = result.get("message", {}).get("content", "")
            
            if not ai_response:
                error_msg = "Empty response from Ollama"
                logger.error(error_msg)
                raise OllamaError(error_msg, error_code="EMPTY_RESPONSE")
            
            logger.info(f"Generated response: {ai_response[:100]}...")
            return ai_response.strip()
            
        except requests.exceptions.Timeout:
            error_msg = f"Ollama request timeout after {self.timeout} seconds"
            logger.error(error_msg)
            raise OllamaError(error_msg, error_code="TIMEOUT")
            
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to Ollama service"
            logger.error(error_msg)
            raise ServiceUnavailableError(error_msg, error_code="OLLAMA_UNAVAILABLE")
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Ollama request failed: {str(e)}"
            logger.error(error_msg)
            raise OllamaError(error_msg, error_code="REQUEST_FAILED")
            
        except Exception as e:
            error_msg = f"Unexpected error in Ollama service: {str(e)}"
            logger.error(error_msg)
            raise OllamaError(error_msg, error_code="UNEXPECTED_ERROR")
    
    def _build_conversation_context(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        Build conversation context for Ollama
        
        Args:
            user_message: Current user message
            conversation_history: Previous messages
            user_context: User context information
            
        Returns:
            List of messages for Ollama
        """
        messages = []
        
        # Add system prompt with user context
        system_message = self.system_prompt
        
        if user_context:
            user_name = user_context.get("name", "Usuario")
            user_phone = user_context.get("phone", "")
            user_language = user_context.get("language", "es")
            
            context_info = f"\n\nContexto del usuario:\n"
            context_info += f"- Nombre: {user_name}\n"
            context_info += f"- Teléfono: {user_phone}\n"
            context_info += f"- Idioma preferido: {user_language}\n"
            
            system_message += context_info
        
        messages.append({
            "role": "system",
            "content": system_message
        })
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                role = "user" if msg.get("direction") == "incoming" else "assistant"
                content = msg.get("content", "")
                
                if content:
                    messages.append({
                        "role": role,
                        "content": content
                    })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def check_health(self) -> bool:
        """
        Check if Ollama service is healthy
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]
                
                if self.model in model_names:
                    logger.info(f"Ollama service is healthy, model {self.model} available")
                    return True
                else:
                    logger.warning(f"Model {self.model} not found in available models: {model_names}")
                    return False
            else:
                logger.warning(f"Ollama health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Ollama health check error: {str(e)}")
            return False
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available models
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]
                logger.info(f"Available models: {model_names}")
                return model_names
            else:
                logger.error(f"Failed to get models: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting models: {str(e)}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """
        Pull a model to Ollama
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Pulling model: {model_name}")
            
            payload = {"name": model_name}
            response = requests.post(
                f"{self.base_url}/api/pull",
                json=payload,
                timeout=300  # 5 minutes timeout for model pulling
            )
            
            if response.status_code == 200:
                logger.info(f"Model {model_name} pulled successfully")
                return True
            else:
                logger.error(f"Failed to pull model {model_name}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {str(e)}")
            return False
    
    def generate_summary(self, messages: List[str], max_length: int = 200) -> str:
        """
        Generate a summary of conversation messages
        
        Args:
            messages: List of messages to summarize
            max_length: Maximum length of summary
            
        Returns:
            Generated summary
        """
        if not messages:
            return ""
        
        try:
            conversation_text = "\n".join(messages[-20:])  # Last 20 messages
            
            summary_prompt = f"""
            Por favor, genera un resumen conciso de la siguiente conversación en máximo {max_length} caracteres:

            {conversation_text}

            Resumen:
            """
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres un asistente que genera resúmenes concisos de conversaciones."
                    },
                    {
                        "role": "user",
                        "content": summary_prompt
                    }
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": max_length
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get("message", {}).get("content", "")
                return summary.strip()[:max_length]
            else:
                logger.error(f"Failed to generate summary: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return ""