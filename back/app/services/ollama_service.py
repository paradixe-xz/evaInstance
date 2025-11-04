"""
Ollama AI service for generating responses
"""

import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

# Disable ollama client to avoid HTTP daemon calls
ollama_client = None

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
        # Ensure ollama client targets the configured host
        try:
            os.environ["OLLAMA_HOST"] = self.base_url
        except Exception:
            pass
        
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
            
            # Use direct ollama CLI - same logic as working simple server
            import subprocess
            
            # Build prompt from messages
            prompt_parts = []
            for msg in messages:
                if msg["role"] == "system":
                    prompt_parts.append(f"System: {msg['content']}")
                elif msg["role"] == "user":
                    prompt_parts.append(f"User: {msg['content']}")
                elif msg["role"] == "assistant":
                    prompt_parts.append(f"Assistant: {msg['content']}")
            
            full_prompt = "\n".join(prompt_parts) + "\nAssistant:"
            
            # Try models in order of preference (same as working server)
            models_to_try = [
                self.model,
                f"{self.model}:latest",
                "emma",
                "emma:latest",
                "emma-medium"
            ]
            
            ai_response = None
            for model_name in models_to_try:
                try:
                    logger.info(f"Trying model: {model_name}")
                    cmd = ["ollama", "run", model_name, full_prompt]
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        encoding='utf-8'
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        ai_response = result.stdout.strip()
                        logger.info(f"✅ Success with model: {model_name}")
                        break
                    else:
                        logger.warning(f"❌ Failed with model {model_name}: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    logger.warning(f"⏰ Timeout with model: {model_name}")
                    continue
                except Exception as e:
                    logger.warning(f"💥 Error with model {model_name}: {e}")
                    continue
            
            if not ai_response:
                error_msg = f"All models failed. Tried: {models_to_try}"
                logger.error(error_msg)
                raise OllamaError(error_msg, error_code="ALL_MODELS_FAILED")
            
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
                # Prefer explicit role if provided; fall back to direction metadata
                role = msg.get("role")
                if not role:
                    direction = msg.get("direction")
                    if direction:
                        role = "user" if direction.lower() == "incoming" else "assistant"
                role = (role or "assistant").lower()

                if role not in {"user", "assistant", "system"}:
                    role = "assistant"

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
            # Use CLI to check health - same as working server
            import subprocess
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                model_names = []
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if parts:
                            model_names.append(parts[0])  # Model name
                
                if self.model in model_names or f"{self.model}:latest" in model_names:
                    logger.info(f"Ollama service is healthy, model {self.model} available")
                    return True
                else:
                    logger.info(f"Model {self.model} not found, but fallback models available: {model_names}")
                    return True  # Still healthy, will use fallback
            else:
                logger.warning(f"Ollama CLI failed: {result.stderr}")
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
            # Use CLI to get models - same as working server
            import subprocess
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                model_names = []
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if parts:
                            model_names.append(parts[0])  # Model name
                
                logger.info(f"Available models: {model_names}")
                return model_names
            else:
                logger.error(f"Failed to get models: {result.stderr}")
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
            logger.info(f"Skipping pull for model: {model_name} (using CLI-only mode)")
            # In CLI-only mode, assume models are already available via ollama list
            # Users should manually install models with: ollama pull <model_name>
            return True
        
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
            
            # Use CLI for summary too - same as working server
            import subprocess
            
            # Build simple prompt for summary
            full_prompt = f"System: Genera un resumen muy breve de esta conversación.\nUser: {summary_prompt}\nAssistant:"
            
            # Try models for summary
            models_to_try = [
                self.model,
                f"{self.model}:latest",
                "emma",
                "emma:latest",
                "emma-medium"
            ]
            
            for model_name in models_to_try:
                try:
                    cmd = ["ollama", "run", model_name, full_prompt]
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        encoding='utf-8'
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        summary = result.stdout.strip()
                        return summary[:max_length]
                        
                except Exception:
                    continue
            
            return ""
                
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return ""
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available Ollama models
        
        Returns:
            List of available models with their details
        """
        try:
            # Use CLI to get models - same as other methods
            import subprocess
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                models = []
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if parts:
                            # Create model dict with basic info
                            models.append({
                                "name": parts[0],
                                "size": parts[2] if len(parts) > 2 else "unknown",
                                "modified_at": " ".join(parts[3:]) if len(parts) > 3 else "unknown",
                                "digest": parts[1] if len(parts) > 1 else "unknown"
                            })
            else:
                logger.error(f"Failed to get models via CLI: {result.stderr}")
                models = []
            
            # Format models for frontend
            formatted_models = []
            for model in models:
                formatted_models.append({
                    "name": model.get("name", ""),
                    "size": model.get("size", 0),
                    "modified_at": model.get("modified_at", ""),
                    "digest": model.get("digest", "")
                })
            
            logger.info(f"Retrieved {len(formatted_models)} Ollama models")
            return formatted_models
            
        except requests.exceptions.Timeout:
            error_msg = f"Ollama request timeout after {self.timeout} seconds"
            logger.error(error_msg)
            raise OllamaError(error_msg, error_code="TIMEOUT")
            
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to Ollama service"
            logger.error(error_msg)
            raise ServiceUnavailableError(error_msg, error_code="OLLAMA_UNAVAILABLE")
            
        except Exception as e:
            error_msg = f"Error listing models: {str(e)}"
            logger.error(error_msg)
            raise OllamaError(error_msg, error_code="UNKNOWN_ERROR")