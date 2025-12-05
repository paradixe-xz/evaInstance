"""
Pydantic models for conversation flows
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class FlowStepQuestion(BaseModel):
    """Model for a question in a flow step"""
    question: str
    field: str
    required: bool = True
    validation: Optional[str] = None

class FlowStep(BaseModel):
    """Model for a single step in a conversation flow"""
    message: str
    next_step: Optional[str] = None
    field: Optional[str] = None
    options: Optional[Dict[str, str]] = None
    questions: Optional[List[FlowStepQuestion]] = None
    end: bool = False
    requires_input: bool = True

class FlowCreate(BaseModel):
    """Model for creating a new flow"""
    name: str
    flow: Dict[str, Any]
    description: Optional[str] = None

class FlowUpdate(BaseModel):
    """Model for updating an existing flow"""
    flow: Dict[str, Any]
    description: Optional[str] = None

class FlowResponse(BaseModel):
    """Response model for a flow"""
    name: str
    flow: Dict[str, Any]
    description: Optional[str] = None

class ConversationState(BaseModel):
    """Model for conversation state"""
    current_step: str
    data: Dict[str, Any] = {}
    start_time: Optional[str] = None
    last_updated: Optional[str] = None

class FlowExecutionResponse(BaseModel):
    """Response model for flow execution"""
    message: str
    step: str
    requires_input: bool
    is_end: bool
    data: Dict[str, Any] = {}
    state: Optional[ConversationState] = None
