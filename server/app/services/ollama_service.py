"""
Ollama AI service for generating responses
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import base64
from pathlib import Path

# Import pdf2image for PDF conversion
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    convert_from_path = None

# Import ollama library
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ollama = None

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
        user_context: Optional[Dict[str, Any]] = None,
        conversation_state: Optional[Dict[str, Any]] = None,
        image_path: Optional[str] = None
    ) -> str:
        """
        Generate AI response using Ollama
        
        Args:
            user_message: User's message
            conversation_history: Previous conversation messages
            user_context: Additional user context (name, preferences, etc.)
            conversation_state: Current conversation state
            image_path: Optional path to image/PDF file for vision models
            
        Returns:
            AI generated response
        """
        
        # If image is provided, use vision model
        if image_path:
            return self.generate_vision_response(user_message, image_path, conversation_history, user_context)
        
        # If we're in AI conversation mode, generate a natural response
        if conversation_state and conversation_state.get("current_step") == "ai_conversation":
            return self._generate_ai_response(user_message, conversation_history, user_context, conversation_state)
            
        # Otherwise, use the default flow response
        return self._generate_flow_response(user_message, conversation_history, user_context)
        
    def _generate_ai_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]],
        user_context: Optional[Dict[str, Any]],
        conversation_state: Dict[str, Any]
    ) -> str:
        """Generate a response when in AI conversation mode"""
        # Build system prompt based on conversation state
        system_prompt = self._build_system_prompt(conversation_state, user_context)
        
        # Build conversation context
        messages = self._build_conversation_context(
            user_message=user_message,
            conversation_history=conversation_history,
            user_context={"system_prompt": system_prompt, **(user_context or {})}
        )
        
        # Generate response
        response = self._call_ollama_api(messages)
        
        return response
        
    def _generate_flow_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]],
        user_context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate a response based on the conversation flow"""
        # Default implementation - can be overridden by specific flow steps
        return "¡Hola! ¿En qué puedo ayudarte hoy?"
        
    def _build_system_prompt(
        self,
        conversation_state: Dict[str, Any],
        user_context: Optional[Dict[str, Any]]
    ) -> str:
        """Build the system prompt based on conversation state"""
        # CRITICAL: Always return None to let the modelfile handle the system prompt
        # The modelfile (Ana, ISA, etc.) has the complete personality and instructions
        # We inject user context (name, phone) directly in the user message instead
        return None
        
    def _call_ollama_api(self, messages: List[Dict[str, str]]) -> str:
        """
        Call Ollama using the Python library
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            Generated response text
            
        Raises:
            OllamaError: If there's an error generating the response
            ServiceUnavailableError: If the Ollama service is not available
        """
        try:
            if not OLLAMA_AVAILABLE:
                raise ServiceUnavailableError("Ollama library not available. Install with: pip install ollama")
            
            logger.info(f"Calling Ollama with model: {self.model}")
            
            # Use ollama library to chat
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            )
            
            # Extract the response content
            if response and "message" in response and "content" in response["message"]:
                ai_response = response["message"]["content"].strip()
                logger.info(f"✅ Got response from Ollama: {ai_response[:100]}...")
                return ai_response
            else:
                error_msg = f"Unexpected response format from Ollama: {response}"
                logger.error(error_msg)
                raise OllamaError(error_msg)
                
        except Exception as e:
            error_msg = f"Error calling Ollama: {str(e)}"
            logger.error(error_msg)
            raise OllamaError(error_msg)
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
            # For "ema" model, don't include system prompt - let modelfile handle it
            # Also filter out any assistant messages that mention seguros/insurance
            prompt_parts = []
            for msg in messages:
                if msg["role"] == "system":
                    # Only include system prompt if it's not the "isa" model
                    # The "isa" modelfile already has the system prompt defined
                    if self.model != "isa" and msg.get("content"):
                        prompt_parts.append(f"System: {msg['content']}")
                elif msg["role"] == "user":
                    # Always include user messages
                    prompt_parts.append(f"User: {msg['content']}")
                elif msg["role"] == "assistant":
                    # Filter out assistant messages that mention seguros/insurance
                    content = msg.get("content", "")
                    if not any(word in content.lower() for word in ["seguro", "insurance", "vive tranqui", "venzamos", "peludito"]):
                        prompt_parts.append(f"Assistant: {content}")
                    else:
                        logger.warning(f"Filtered out contaminated assistant message: {content[:50]}...")
            
            full_prompt = "\n".join(prompt_parts) + "\nAssistant:"
            
            # Try models in order of preference (same as working server)
            models_to_try = [
                self.model,
                f"{self.model}:latest",
                "isa",
                "isa:latest"
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
        
        # CRITICAL: Let the modelfile handle the system prompt completely
        # Do NOT add any system messages - the modelfile (Ana, ISA, etc.) already has it
        
        # Add conversation history (clean, no modifications)
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
        
        # Prepare current user message
        # If we have user context (name, phone), inject it naturally in the FIRST message only
        final_user_message = user_message
        
        if user_context and len(messages) == 0:  # Only on first message of conversation
            context_parts = []
            if "name" in user_context and user_context["name"]:
                context_parts.append(f"[Cliente: {user_context['name']}]")
            if "phone" in user_context and user_context["phone"]:
                context_parts.append(f"[Tel: {user_context['phone']}]")
            
            # Add context prefix only if we have it
            if context_parts:
                context_str = " ".join(context_parts)
                final_user_message = f"{context_str}\n{user_message}"
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": final_user_message
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
                "isa",
                "isa:latest"
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
    
    def generate_vision_response(
        self,
        user_message: str,
        image_path: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate AI response for images/PDFs using vision models
        
        Args:
            user_message: User's message/question about the image
            image_path: Path to the image or PDF file
            conversation_history: Previous conversation messages
            user_context: Additional user context
            
        Returns:
            AI generated response about the image
        """
        try:
            if not OLLAMA_AVAILABLE:
                raise ServiceUnavailableError("Ollama library not available")
            
            logger.info(f"Generating vision response for file: {image_path}")
            
            # Check if file is PDF
            is_pdf = image_path.lower().endswith('.pdf')
            images_base64 = []
            
            if is_pdf:
                # Convert PDF to images
                if not PDF2IMAGE_AVAILABLE:
                    logger.warning("pdf2image not available, falling back to text extraction")
                    raise OllamaError("PDF to image conversion not available. Install pdf2image: pip install pdf2image")
                
                logger.info(f"Converting PDF to images: {image_path}")
                try:
                    # Convert PDF pages to images
                    images = convert_from_path(image_path, dpi=200)
                    logger.info(f"Converted PDF to {len(images)} images")
                    
                    # Convert each page to base64
                    import io
                    for i, img in enumerate(images):
                        # Convert PIL Image to bytes
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='PNG')
                        img_byte_arr = img_byte_arr.getvalue()
                        
                        # Encode to base64
                        img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
                        images_base64.append(img_base64)
                        
                        # Limit to first 5 pages to avoid token limits
                        if i >= 4:
                            logger.info(f"Limiting to first 5 pages of PDF")
                            break
                    
                except Exception as e:
                    error_msg = f"Error converting PDF to images: {str(e)}"
                    logger.error(error_msg)
                    raise OllamaError(error_msg)
            else:
                # Read and encode single image to base64
                with open(image_path, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')
                    images_base64.append(image_data)
            
            # Build messages with images
            messages = []
            
            # Add conversation history if available (text only)
            if conversation_history:
                for msg in conversation_history[-5:]:  # Last 5 messages for context
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if content and role in ["user", "assistant"]:
                        messages.append({
                            "role": role,
                            "content": content
                        })
            
            # Add current message with images
            messages.append({
                "role": "user",
                "content": user_message,
                "images": images_base64
            })
            
            logger.info(f"Calling vision model: {self.model} with {len(images_base64)} image(s)")
            
            # Call Ollama with vision support
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            )
            
            if response and "message" in response:
                ai_response = response["message"]["content"]
                logger.info(f"✅ Got vision response: {ai_response[:100]}...")
                return ai_response
            else:
                error_msg = f"Unexpected response format from vision model: {response}"
                logger.error(error_msg)
                raise OllamaError(error_msg)
                
        except FileNotFoundError:
            error_msg = f"File not found: {image_path}"
            logger.error(error_msg)
            raise OllamaError(error_msg)
        except Exception as e:
            error_msg = f"Error calling vision model: {str(e)}"
            logger.error(error_msg)
            raise OllamaError(error_msg)
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available Ollama models
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