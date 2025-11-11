"""
Service for managing conversation state and flow
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
from pathlib import Path

from ..core.logging import get_logger
from ..config.conversation_flows import get_flow, DEFAULT_ISA_FLOW

logger = get_logger(__name__)

class ConversationService:
    """Service for managing conversation state and flow"""
    
    def __init__(self, conversation_flow: str = "isa"):
        """
        Initialize conversation service with a specific flow
        
        Args:
            conversation_flow: Name of the conversation flow to use (default: 'isa')
        """
        self.flow = get_flow(conversation_flow)
        self.conversation_states = {}
        self.flows_dir = Path("conversation_flows")
        self.flows_dir.mkdir(exist_ok=True)
        
    def get_conversation_state(self, user_id: str) -> Dict[str, Any]:
        """Get or initialize conversation state for a user"""
        if user_id not in self.conversation_states:
            return self.initialize_conversation(user_id)
        return self.conversation_states[user_id]
        
    def update_conversation_state(self, user_id: str, updates: Dict[str, Any]) -> None:
        """Update conversation state for a user"""
        if user_id not in self.conversation_states:
            self.initialize_conversation(user_id)
        self.conversation_states[user_id].update(updates)
        self.conversation_states[user_id]["last_updated"] = datetime.utcnow().isoformat()
        
    def get_next_step(self, user_id: str, user_input: str) -> Dict[str, Any]:
        """
        Get the next step in the conversation flow based on user input
        
        Args:
            user_id: Unique identifier for the user
            user_input: User's input message
            
        Returns:
            Dict containing the response and updated state
        """
        state = self.get_conversation_state(user_id)
        current_step = state.get("current_step", "initial_greeting")
        step_data = self.flow.get(current_step, {})
        
        # Initialize response
        response = {"message": "", "next_step": None, "data": state.get("data", {})}
        
        # Handle AI conversation mode
        if current_step == "ai_conversation":
            response["message"] = None  # Will be handled by OllamaService
            return response
            
        # Handle data authorization
        if current_step == "data_authorization" and user_input.lower() in ("sí", "si", "s"):
            self.update_conversation_state(user_id, {"current_step": "ai_conversation"})
            response["message"] = None  # Will be handled by OllamaService
            return response
            
        # Handle insurance selection
        if current_step == "insurance_selection":
            if user_input.isdigit() and 1 <= int(user_input) <= 3:
                insurance_type = {
                    "1": "Seguro de Hogar 'Vive Tranqui'",
                    "2": "Seguro Oncológico 'Venzamos'",
                    "3": "Seguro para Mascotas 'Peludito'"
                }.get(user_input, "seguro")
                self.update_conversation_state(user_id, {
                    "current_step": "ai_conversation",
                    "data": {**state.get("data", {}), "selected_insurance": insurance_type}
                })
                response["message"] = None  # Will be handled by OllamaService
                return response
        
        # Handle other steps with predefined messages
        if "message" in step_data:
            response["message"] = step_data["message"]
            
            # Add options if available
            if "options" in step_data:
                options = step_data["options"]
                if isinstance(options, dict):
                    response["message"] += "\n\nOpciones:\n" + "\n".join([f"{k}. {v}" for k, v in options.items()])
                elif isinstance(options, list):
                    response["message"] += "\n\nOpciones:\n" + "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
            
            # Update next step
            if "next_step" in step_data:
                next_step = step_data["next_step"]
                if isinstance(next_step, dict):
                    if user_input.lower() in next_step:
                        response["next_step"] = next_step[user_input.lower()]
                else:
                    response["next_step"] = next_step
        
        # Update conversation state
        if response["next_step"]:
            self.update_conversation_state(user_id, {"current_step": response["next_step"]})
            
        return response
    
    def initialize_conversation(self, user_id: str) -> Dict[str, Any]:
        """
        Initialize a new conversation
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Initial conversation state
        """
        self.conversation_states[user_id] = {
            "current_step": "initial_greeting",
            "data": {},
            "start_time": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat()
        }
        return self.conversation_states[user_id]
    
    def list_available_flows(self) -> List[str]:
        """
        List all available conversation flow files
        
        Returns:
            List of flow names
        """
        try:
            # Get all JSON files in the flows directory
            flow_files = list(self.flows_dir.glob("*.json"))
            # Return filenames without extension
            return [f.stem for f in flow_files]
        except Exception as e:
            logger.error(f"Error listing flows: {str(e)}")
            return []
    
    def load_flow_from_file(self, flow_name: str) -> Dict[str, Any]:
        """
        Load a conversation flow from a JSON file
        
        Args:
            flow_name: Name of the flow to load (without .json extension)
            
        Returns:
            Dictionary containing the flow configuration
            
        Raises:
            FileNotFoundError: If the flow file doesn't exist
        """
        flow_path = self.flows_dir / f"{flow_name}.json"
        if not flow_path.exists():
            # If the flow doesn't exist, return the default ISA flow
            if flow_name == "isa":
                return DEFAULT_ISA_FLOW
            raise FileNotFoundError(f"Flow '{flow_name}' not found")
            
        with open(flow_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_flow_to_file(self, flow_name: str, flow_data: Dict[str, Any]) -> Path:
        """
        Save a conversation flow to a JSON file
        
        Args:
            flow_name: Name of the flow to save
            flow_data: Flow configuration data
            
        Returns:
            Path to the saved flow file
        """
        flow_path = self.flows_dir / f"{flow_name}.json"
        with open(flow_path, 'w', encoding='utf-8') as f:
            json.dump(flow_data, f, indent=2, ensure_ascii=False)
        return flow_path
    
    def get_next_message(self, user_id: str, user_input: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the next message in the conversation flow
        
        Args:
            user_id: Unique identifier for the user
            user_input: User's input (if any)
            
        Returns:
            Dict containing the message and next step information
        """
        if user_id not in self.conversation_states:
            self.initialize_conversation(user_id)
        
        state = self.conversation_states[user_id]
        current_step = state["current_step"]
        
        # Update last activity timestamp
        state["last_updated"] = datetime.utcnow().isoformat()
        
        # Handle user input if provided
        if user_input is not None:
            self._process_user_input(user_id, current_step, user_input)
        
        # Get next step
        next_step = self._get_next_step(user_id, current_step, user_input)
        
        # Update state
        state["current_step"] = next_step
        
        # Get message for next step
        step_data = self.flow.get(next_step, {"message": "¡Hola! ¿En qué puedo ayudarte hoy?"})
        
        return {
            "message": step_data.get("message", "¡Hola! ¿En qué puedo ayudarte hoy?"),
            "step": next_step,
            "requires_input": not step_data.get("end", False),
            "is_end": step_data.get("end", False),
            "data": state["data"]
        }
    
    def _process_user_input(self, user_id: str, current_step: str, user_input: str) -> None:
        """Process and store user input based on current step"""
        step_data = self.flow.get(current_step, {})
        
        # Handle data collection if specified in the flow
        if "field" in step_data:
            field = step_data["field"]
            self.conversation_states[user_id]["data"][field] = user_input
        
        # Handle multiple questions in a step
        if "questions" in step_data:
            question_index = self.conversation_states[user_id].get("question_index", 0)
            questions = step_data["questions"]
            
            if question_index < len(questions):
                field = questions[question_index].get("field")
                if field:
                    self.conversation_states[user_id]["data"][field] = user_input
                
                # Move to next question or next step
                if question_index < len(questions) - 1:
                    self.conversation_states[user_id]["question_index"] = question_index + 1
                else:
                    # All questions answered, move to next step
                    if "next_step" in step_data:
                        self.conversation_states[user_id]["current_step"] = step_data["next_step"]
                    del self.conversation_states[user_id]["question_index"]
    
    def _get_next_step(self, user_id: str, current_step: str, user_input: Optional[str] = None) -> str:
        """Determine the next step in the conversation flow"""
        step_data = self.flow.get(current_step, {})
        
        # If step has options and user provided input, use it to determine next step
        if user_input and "options" in step_data and "next_step" in step_data and isinstance(step_data["next_step"], dict):
            return step_data["next_step"].get(user_input, current_step)
        
        # If step has a direct next step
        if "next_step" in step_data and isinstance(step_data["next_step"], str):
            return step_data["next_step"]
        
        # Default to current step if no next step is defined
        return current_step
    
    def save_flow_to_file(self, flow_name: str, flow_data: Dict[str, Any]) -> str:
        """
        Save a conversation flow to a JSON file
        
        Args:
            flow_name: Name of the flow
            flow_data: Flow data to save
            
        Returns:
            Path to the saved file
        """
        file_path = self.flows_dir / f"{flow_name}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(flow_data, f, ensure_ascii=False, indent=2)
        return str(file_path)
    
    def load_flow_from_file(self, flow_name: str) -> Dict[str, Any]:
        """
        Load a conversation flow from a JSON file
        
        Args:
            flow_name: Name of the flow to load
            
        Returns:
            Loaded flow data
        """
        file_path = self.flows_dir / f"{flow_name}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Flow file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_available_flows(self) -> list:
        """
        List all available conversation flows
        
        Returns:
            List of available flow names
        """
        return [f.stem for f in self.flows_dir.glob("*.json")]
