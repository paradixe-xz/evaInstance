"""
Agent service for managing AI agents and Ollama model creation
"""

import os
import json
import tempfile
import subprocess
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.exceptions import AgentError, OllamaError, ServiceUnavailableError
from ..models.agent import Agent
from ..repositories.agent_repository import AgentRepository
from ..schemas.agent import AgentCreate, AgentUpdate, OllamaModelCreate
from .ollama_service import OllamaService
from .rag_service import rag_service

logger = get_logger(__name__)
settings = get_settings()


class AgentService:
    """Service for managing AI agents and Ollama integration"""
    
    def __init__(self, db: Session):
        self.db = db
        self.agent_repo = AgentRepository(db)
        self.ollama_service = OllamaService()
        self.base_url = settings.ollama_base_url
        
    def create_agent(self, agent_data: AgentCreate, creator_id: int) -> Agent:
        """
        Create a new agent
        
        Args:
            agent_data: Agent creation data
            creator_id: ID of the user creating the agent
            
        Returns:
            Created agent
        """
        try:
            # Prepare agent data
            agent_dict = agent_data.model_dump()
            agent_dict['creator_id'] = creator_id
            agent_dict['created_at'] = datetime.utcnow()
            agent_dict['updated_at'] = datetime.utcnow()
            
            # Create agent in database
            agent = self.agent_repo.create(agent_dict)
            
            logger.info(f"Agent created successfully: {agent.name} (ID: {agent.id})")
            return agent
            
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise AgentError(f"Failed to create agent: {str(e)}")
    
    def create_ollama_model(self, model_data: OllamaModelCreate, creator_id: int) -> Dict[str, Any]:
        """
        Create a custom Ollama model and save it as an agent
        
        Args:
            model_data: Ollama model creation data
            creator_id: ID of the user creating the model
            
        Returns:
            Dictionary with model creation results
        """
        try:
            # Generate unique model name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ollama_model_name = f"{model_data.name.lower().replace(' ', '_')}_{timestamp}"
            
            # Create modelfile content
            modelfile_content = self._generate_modelfile(model_data, ollama_model_name)
            
            # Create temporary modelfile
            modelfile_path = self._create_temporary_modelfile(modelfile_content)
            
            try:
                # Create Ollama model
                success = self._create_ollama_model_command(ollama_model_name, modelfile_path)
                
                if not success:
                    raise AgentError("Failed to create Ollama model")
                
                logger.info(f"Ollama model created successfully: {ollama_model_name}")
                
                # Save the model as an agent in the database
                agent_data = {
                    'name': model_data.name,
                    'description': f"Custom Ollama model based on {model_data.base_model}",
                    'agent_type': 'whatsapp',
                    'status': 'active',
                    'is_active': True,
                    'model': ollama_model_name,
                    'temperature': model_data.temperature,
                    'max_tokens': 2048,  # Default value
                    'system_prompt': model_data.system_prompt,
                    'is_ollama_model': True,
                    'ollama_model_name': ollama_model_name,
                    'base_model': model_data.base_model,
                    'num_ctx': model_data.num_ctx,
                    'modelfile_content': modelfile_content,
                    'custom_template': model_data.custom_template,
                    'creator_id': creator_id,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                
                # Create agent in database
                agent = self.agent_repo.create(agent_data)
                
                return {
                    "success": True,
                    "agent_id": agent.id,
                    "model_name": ollama_model_name,
                    "base_model": model_data.base_model,
                    "temperature": model_data.temperature,
                    "num_ctx": model_data.num_ctx,
                    "system_prompt": model_data.system_prompt,
                    "custom_template": model_data.custom_template,
                    "modelfile_content": modelfile_content,
                    "message": f"Ollama model '{ollama_model_name}' created successfully"
                }
                
            finally:
                # Clean up temporary file
                if os.path.exists(modelfile_path):
                    os.remove(modelfile_path)
                    
        except Exception as e:
            logger.error(f"Error creating Ollama model: {str(e)}")
            raise AgentError(f"Failed to create Ollama model: {str(e)}")
    
    def _generate_modelfile(self, model_data: OllamaModelCreate, model_name: str) -> str:
        """
        Generate Ollama modelfile content
        
        Args:
            model_data: Model creation data
            model_name: Generated model name
            
        Returns:
            Modelfile content as string
        """
        modelfile_lines = [
            f"FROM {model_data.base_model}",
            "",
            "# Set the temperature for creativity (higher = more creative, lower = more coherent)",
            f"PARAMETER temperature {model_data.temperature}",
            "",
            "# Set the context window size (how many tokens the LLM can use as context)",
            f"PARAMETER num_ctx {model_data.num_ctx}",
            ""
        ]
        
        # Add system prompt
        modelfile_lines.extend([
            "# Define a custom system message to guide the model's persona or role",
            f'SYSTEM """{model_data.system_prompt}"""',
            ""
        ])
        
        # Add custom template if provided
        if model_data.custom_template:
            modelfile_lines.extend([
                "# Define a custom prompt template for consistent interaction",
                f'TEMPLATE """{model_data.custom_template}"""'
            ])
        
        return "\n".join(modelfile_lines)
    
    def _create_temporary_modelfile(self, content: str) -> str:
        """
        Create a temporary modelfile
        
        Args:
            content: Modelfile content
            
        Returns:
            Path to temporary file
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.modelfile', delete=False, encoding='utf-8') as f:
            f.write(content)
            return f.name
    
    def _create_ollama_model_command(self, model_name: str, modelfile_path: str) -> bool:
        """
        Create an Ollama model using the CLI command
        
        Args:
            model_name: Name for the new model
            modelfile_path: Path to the modelfile
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify modelfile exists and is readable
            if not os.path.exists(modelfile_path):
                logger.error(f"Modelfile not found at path: {modelfile_path}")
                return False
                
            # Read modelfile content for logging
            with open(modelfile_path, 'r', encoding='utf-8') as f:
                modelfile_content = f.read()
                
            logger.info(f"📄 Modelfile content for '{model_name}':\n{modelfile_content}")
            
            # Build and log the command
            cmd = ["ollama", "create", model_name, "-f", modelfile_path]
            logger.info(f"🚀 Executing command: {' '.join(cmd)}")
            
            # Execute the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=True,  # Use shell=True for better Windows compatibility
                timeout=300  # 5 minutes timeout
            )
            
            # Log command output
            if result.stdout:
                logger.info(f"✅ Command output:\n{result.stdout}")
            if result.stderr:
                logger.error(f"❌ Command error output:\n{result.stderr}")
            
            if result.returncode == 0:
                logger.info(f"✅ Ollama model '{model_name}' created successfully")
                return True
            else:
                # Check if model already exists
                if "already exists" in result.stderr.lower():
                    logger.warning(f"⚠️ Model '{model_name}' already exists")
                    return True
                    
                logger.error(f"❌ Failed to create Ollama model '{model_name}'")
                logger.error(f"Exit code: {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired as e:
            logger.error(f"⏰ Timeout creating Ollama model '{model_name}': {str(e)}")
            return False
            
        except FileNotFoundError as e:
            logger.error(f"🔍 Command not found: {str(e)}")
            logger.error("Make sure 'ollama' is installed and in your PATH")
            return False
            
        except Exception as e:
            logger.error(f"❌ Unexpected error creating Ollama model: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return False

    def get_agent_by_id(self, agent_id: int) -> Optional[Agent]:
        """Get agent by ID"""
        return self.agent_repo.get(agent_id)
    
    def get_agents_by_user(self, user_id: int) -> List[Agent]:
        """Get all agents created by a user"""
        return self.agent_repo.get_by_user(user_id)
    
    def get_agents_by_campaign(self, campaign_id: int) -> List[Agent]:
        """Get all agents for a campaign"""
        return self.agent_repo.get_by_campaign(campaign_id)
    
    def update_agent(self, agent_id: int, agent_data: AgentUpdate) -> Optional[Agent]:
        """
        Update an existing agent
        
        Args:
            agent_id: ID of the agent to update
            agent_data: Updated agent data
            
        Returns:
            Updated agent or None if not found
        """
        try:
            update_dict = agent_data.model_dump(exclude_unset=True)
            update_dict['updated_at'] = datetime.utcnow()
            
            agent = self.agent_repo.update(agent_id, update_dict)
            
            if agent:
                logger.info(f"Agent updated successfully: {agent.name} (ID: {agent.id})")
            
            return agent
            
        except Exception as e:
            logger.error(f"Error updating agent {agent_id}: {str(e)}")
            raise AgentError(f"Failed to update agent: {str(e)}")
    
    def delete_agent(self, agent_id: int) -> bool:
        """
        Delete an agent and optionally its Ollama model
        
        Args:
            agent_id: ID of the agent to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            agent = self.agent_repo.get(agent_id)
            if not agent:
                return False
            
            # If it's an Ollama model, try to delete it
            if agent.is_ollama_model and agent.ollama_model_name:
                self._delete_ollama_model(agent.ollama_model_name)
            
            # Delete agent from database
            success = self.agent_repo.delete(agent_id)
            
            if success:
                logger.info(f"Agent deleted successfully: {agent.name} (ID: {agent.id})")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting agent {agent_id}: {str(e)}")
            raise AgentError(f"Failed to delete agent: {str(e)}")
    
    def _delete_ollama_model(self, model_name: str) -> bool:
        """
        Delete an Ollama model
        
        Args:
            model_name: Name of the model to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = ["ollama", "rm", model_name]
            
            logger.info(f"Deleting Ollama model: {model_name}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info(f"Ollama model '{model_name}' deleted successfully")
                return True
            else:
                logger.warning(f"Failed to delete Ollama model '{model_name}': {result.stderr}")
                return False
                
        except Exception as e:
            logger.warning(f"Error deleting Ollama model '{model_name}': {str(e)}")
            return False
    
    def test_agent(self, agent_id: int, test_message: str) -> str:
        """
        Test an agent with a message
        
        Args:
            agent_id: ID of the agent to test
            test_message: Test message
            
        Returns:
            Agent response
        """
        try:
            agent = self.agent_repo.get(agent_id)
            if not agent:
                raise AgentError("Agent not found")
            
            # Use the agent's model for generation
            original_model = self.ollama_service.model
            original_system_prompt = self.ollama_service.system_prompt
            original_temperature = self.ollama_service.temperature
            
            try:
                # Temporarily configure ollama service for this agent
                self.ollama_service.model = agent.model
                self.ollama_service.system_prompt = agent.system_prompt
                self.ollama_service.temperature = agent.temperature
                
                # Generate response
                response = self.ollama_service.generate_response(test_message)
                
                # Update agent metrics
                self.agent_repo.update_last_used(agent_id)
                
                return response
                
            finally:
                # Restore original configuration
                self.ollama_service.model = original_model
                self.ollama_service.system_prompt = original_system_prompt
                self.ollama_service.temperature = original_temperature
                
        except Exception as e:
            logger.error(f"Error testing agent {agent_id}: {str(e)}")
            raise AgentError(f"Failed to test agent: {str(e)}")
    
    def get_available_base_models(self) -> List[str]:
        """Get list of available base models for Ollama"""
        return self.ollama_service.get_available_models()
    
    def get_ollama_agents(self, user_id: int) -> List[Agent]:
        """Get all Ollama agents for a specific user"""
        return self.agent_repo.get_ollama_agents(user_id)
    
    def activate_agent(self, agent_id: int) -> bool:
        """Activate an agent"""
        return self.agent_repo.activate(agent_id)
    
    def deactivate_agent(self, agent_id: int) -> bool:
        """Deactivate an agent"""
        return self.agent_repo.deactivate(agent_id)
    
    def update_ollama_model(self, agent_id: int, model_data: 'OllamaModelCreate', user_id: int) -> dict:
        """
        Update an existing Ollama model
        
        Args:
            agent_id: ID of the agent to update
            model_data: Model configuration data
            user_id: ID of the user updating the model
            
        Returns:
            Dictionary with update result
        """
        try:
            # Get the existing agent
            agent = self.get_agent_by_id(agent_id)
            if not agent:
                raise AgentError("Agent not found")
            
            if agent.creator_id != user_id:
                raise AgentError("Unauthorized to update this agent")
            
            if not agent.is_ollama_model:
                raise AgentError("Agent is not an Ollama model")
            
            # Generate new unique model name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_model_name = f"{model_data.name.lower().replace(' ', '_')}_{timestamp}"
            
            # Create modelfile content
            modelfile_content = self._generate_modelfile(model_data, new_model_name)
            
            # Create temporary modelfile
            modelfile_path = self._create_temporary_modelfile(modelfile_content)
            
            try:
                # Create new Ollama model
                success = self._create_ollama_model_command(new_model_name, modelfile_path)
                
                if not success:
                    raise OllamaError("Failed to create updated Ollama model")
                
                # Update agent in database
                update_data = {
                    'name': model_data.name,
                    'description': f"Modelo Ollama personalizado basado en {model_data.base_model}",
                    'ollama_model_name': new_model_name,
                    'base_model': model_data.base_model,
                    'modelfile_content': modelfile_content,
                    'ollama_parameters': {
                        'temperature': model_data.temperature,
                        'num_ctx': model_data.num_ctx,
                        'system_prompt': model_data.system_prompt,
                        'custom_template': model_data.custom_template
                    },
                    'updated_at': datetime.now()
                }
                
                updated_agent = self.agent_repo.update(agent_id, update_data)
                
                if not updated_agent:
                    raise AgentError("Failed to update agent in database")
                
                logger.info(f"Ollama model updated successfully: {new_model_name}")
                
                return {
                    "success": True,
                    "agent_id": agent_id,
                    "model_name": new_model_name,
                    "display_name": model_data.name,
                    "base_model": model_data.base_model,
                    "temperature": model_data.temperature,
                    "num_ctx": model_data.num_ctx,
                    "system_prompt": model_data.system_prompt,
                    "custom_template": model_data.custom_template,
                    "message": f"Modelo '{model_data.name}' actualizado exitosamente"
                }
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(modelfile_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary modelfile: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error updating Ollama model: {str(e)}")
            if isinstance(e, (AgentError, OllamaError)):
                raise
            raise AgentError(f"Failed to update Ollama model: {str(e)}")
    
    def chat_with_ollama_model(
        self, 
        agent_id: int, 
        message: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Chat with an Ollama model using the agent's configuration
        
        Args:
            agent_id: ID of the agent/model to chat with
            message: User's message
            conversation_history: Previous conversation messages
            
        Returns:
            AI response from the Ollama model
        """
        try:
            # Get the agent
            agent = self.get_agent_by_id(agent_id)
            if not agent:
                raise AgentError("Agent not found")
            
            if not agent.is_ollama_model:
                raise AgentError("Agent is not an Ollama model")
            
            # Prepare the conversation context
            messages = []
            
            # Add system prompt from agent configuration
            if agent.system_prompt:
                messages.append({
                    "role": "system",
                    "content": agent.system_prompt
                })
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Use direct CLI instead of HTTP daemon to avoid context issues
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
            
            logger.info(f"Chatting with Ollama model via CLI: {agent.ollama_model_name}")
            
            # Try with exact model name first, then with :latest, then fallback to base models
            model_names_to_try = [agent.ollama_model_name]
            if ":" not in agent.ollama_model_name:
                model_names_to_try.append(f"{agent.ollama_model_name}:latest")
            # Fallback to known working models
            model_names_to_try.extend(["llama3.2:3b", "llama3.2", "llama3"])
            
            ai_response = None
            for model_name in model_names_to_try:
                try:
                    cmd = ["ollama", "run", model_name, full_prompt]
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        encoding='utf-8'
                    )
                    
                    if result.returncode == 0:
                        ai_response = result.stdout.strip()
                        logger.info(f"Successfully used model: {model_name}")
                        break
                    else:
                        logger.warning(f"Model {model_name} failed: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    logger.warning(f"Model {model_name} timed out")
                    continue
                except Exception as e:
                    logger.warning(f"Model {model_name} error: {str(e)}")
                    continue
            
            if not ai_response:
                error_msg = f"All model attempts failed for {agent.ollama_model_name}"
                logger.error(error_msg)
                raise OllamaError(error_msg)
            
            if not ai_response:
                error_msg = "Empty response from Ollama"
                logger.error(error_msg)
                raise OllamaError(error_msg)
            
            logger.info(f"Generated response from {agent.ollama_model_name}: {ai_response[:100]}...")
            return ai_response.strip()
            
        except requests.exceptions.Timeout:
            error_msg = f"Ollama request timeout after 30 seconds"
            logger.error(error_msg)
            raise OllamaError(error_msg)
            
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to Ollama service"
            logger.error(error_msg)
            raise OllamaError(error_msg)
            
        except Exception as e:
            logger.error(f"Error chatting with Ollama model: {str(e)}")
            if isinstance(e, (AgentError, OllamaError)):
                raise
            raise AgentError(f"Failed to chat with Ollama model: {str(e)}")

    def _resolve_model_name(self, model_name: str) -> str:
        """
        Resolve an Ollama model name against available tags.
        - If model has a tag, return as-is.
        - If no tag, and '<name>:latest' exists, return with ':latest'.
        - Otherwise, return original name.
        """
        try:
            if ":" in model_name:
                return model_name

            resp = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if resp.status_code != 200:
                return model_name

            models = resp.json().get("models", [])
            names = {m.get("name", "") for m in models}

            if model_name in names:
                return model_name

            candidate = f"{model_name}:latest"
            if candidate in names:
                return candidate

            return model_name
        except Exception:
            return model_name
    
    async def chat_with_knowledge_base(
        self, 
        agent_id: int, 
        message: str, 
        conversation_history: List[Dict[str, str]] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Chat with an Ollama model enhanced with Knowledge Base (RAG)
        
        Args:
            agent_id: ID of the agent/model to chat with
            message: User's message
            conversation_history: Previous conversation messages
            db: Database session for knowledge base access
            
        Returns:
            Dict containing AI response and knowledge base information
        """
        try:
            # Get the agent
            agent = self.get_agent_by_id(agent_id)
            if not agent:
                raise AgentError("Agent not found")
            
            if not agent.is_ollama_model:
                raise AgentError("Agent is not an Ollama model")
            
            # Enhance prompt with knowledge base if available
            enhanced_data = await rag_service.enhance_prompt_with_knowledge(
                agent_id=agent_id,
                user_message=message,
                db=db
            )
            
            # Use enhanced prompt if knowledge is available
            final_message = enhanced_data.get("enhanced_prompt", message)
            
            # Prepare the conversation context
            messages = []
            
            # Add system prompt from agent configuration
            if agent.system_prompt:
                messages.append({
                    "role": "system",
                    "content": agent.system_prompt
                })
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user message (enhanced with knowledge if available)
            messages.append({
                "role": "user",
                "content": final_message
            })
            
            # Use direct CLI instead of HTTP daemon for KB chat too
            import subprocess
            
            # Build prompt from messages (including enhanced KB context)
            prompt_parts = []
            for msg in messages:
                if msg["role"] == "system":
                    prompt_parts.append(f"System: {msg['content']}")
                elif msg["role"] == "user":
                    prompt_parts.append(f"User: {msg['content']}")
                elif msg["role"] == "assistant":
                    prompt_parts.append(f"Assistant: {msg['content']}")
            
            full_prompt = "\n".join(prompt_parts) + "\nAssistant:"
            
            logger.info(f"Chatting with Ollama model via CLI (with KB): {agent.ollama_model_name}")
            
            # Try with exact model name first, then with :latest, then fallback to base models
            model_names_to_try = [agent.ollama_model_name]
            if ":" not in agent.ollama_model_name:
                model_names_to_try.append(f"{agent.ollama_model_name}:latest")
            # Fallback to known working models
            model_names_to_try.extend(["llama3.2:3b", "llama3.2", "llama3"])
            
            ai_response = None
            for model_name in model_names_to_try:
                try:
                    cmd = ["ollama", "run", model_name, full_prompt]
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        encoding='utf-8'
                    )
                    
                    if result.returncode == 0:
                        ai_response = result.stdout.strip()
                        logger.info(f"Successfully used model: {model_name}")
                        break
                    else:
                        logger.warning(f"Model {model_name} failed: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    logger.warning(f"Model {model_name} timed out")
                    continue
                except Exception as e:
                    logger.warning(f"Model {model_name} error: {str(e)}")
                    continue
            
            if not ai_response:
                error_msg = f"All model attempts failed for {agent.ollama_model_name}"
                logger.error(error_msg)
                raise OllamaError(error_msg)
            
            if not ai_response:
                error_msg = "Empty response from Ollama"
                logger.error(error_msg)
                raise OllamaError(error_msg)
            
            # Format response with sources if knowledge was used
            if enhanced_data.get("has_knowledge"):
                formatted_response = rag_service.format_response_with_sources(
                    ai_response,
                    enhanced_data.get("sources", [])
                )
            else:
                formatted_response = ai_response
            
            logger.info(f"Generated response from {agent.ollama_model_name}: {ai_response[:100]}...")
            
            return {
                "ai_response": formatted_response.strip(),
                "original_response": ai_response.strip(),
                "knowledge_used": enhanced_data.get("has_knowledge", False),
                "sources": enhanced_data.get("sources", []),
                "context": enhanced_data.get("context", ""),
                "knowledge_count": enhanced_data.get("knowledge_used", 0)
            }
            
        except requests.exceptions.Timeout:
            error_msg = f"Ollama request timeout after 30 seconds"
            logger.error(error_msg)
            raise OllamaError(error_msg)
            
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to Ollama service"
            logger.error(error_msg)
            raise OllamaError(error_msg)
            
        except Exception as e:
            logger.error(f"Error chatting with Ollama model (KB): {str(e)}")
            if isinstance(e, (AgentError, OllamaError)):
                raise
            raise AgentError(f"Failed to chat with Ollama model: {str(e)}")

    def stream_chat_with_ollama_model(
        self,
        agent_id: int,
        message: str,
        conversation_history: List[Dict[str, str]] = None
    ):
        """
        Stream chat with an Ollama model using the HTTP API (stream=true).
        Yields NDJSON chunks: {"delta":"..."} and final {"done":true,"full":"..."}
        """
        try:
            agent = self.get_agent_by_id(agent_id)
            if not agent:
                raise AgentError("Agent not found")
            if not agent.is_ollama_model:
                raise AgentError("Agent is not an Ollama model")

            # Build messages
            messages: List[Dict[str, str]] = []
            if agent.system_prompt:
                messages.append({"role": "system", "content": agent.system_prompt})
            if conversation_history:
                messages.extend(conversation_history)
            messages.append({"role": "user", "content": message})

            base_url = settings.ollama_base_url.rstrip("/")
            url = f"{base_url}/api/chat"

            payload = {
                "model": agent.ollama_model_name,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": float(agent.temperature) if agent.temperature is not None else 0.7,
                    "num_ctx": int(agent.num_ctx) if agent.num_ctx else 2048,
                },
            }

            logger.info(f"Streaming chat via Ollama API for model {agent.ollama_model_name}")

            with requests.post(url, json=payload, stream=True, timeout=300) as resp:
                resp.raise_for_status()
                full_text: List[str] = []
                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        # Ollama returns objects with 'message' chunks
                        delta = data.get("message", {}).get("content") or data.get("delta") or ""
                        if delta:
                            full_text.append(delta)
                            yield json.dumps({"delta": delta}) + "\n"
                    except Exception:
                        # Fallback: emit raw line
                        yield json.dumps({"delta": line}) + "\n"
                yield json.dumps({"done": True, "full": "".join(full_text)}) + "\n"

        except requests.exceptions.Timeout:
            err = "Ollama streaming timeout"
            logger.error(err)
            yield json.dumps({"error": err}) + "\n"
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            yield json.dumps({"error": str(e)}) + "\n"