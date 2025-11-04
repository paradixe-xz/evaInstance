"""
Agent schemas
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AgentBase(BaseModel):
    """Base agent schema"""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    agent_type: str = Field(..., pattern="^(calls|whatsapp)$")


class AgentCreate(AgentBase):
    """Agent creation schema"""
    model: str = Field(default="gpt-4")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1000, ge=100, le=4000)
    system_prompt: str = Field(..., min_length=10)
    
    # Ollama specific fields
    is_ollama_model: bool = Field(default=False)
    ollama_model_name: Optional[str] = Field(None, min_length=2, max_length=100)
    base_model: str = Field(default="llama2")
    num_ctx: int = Field(default=4096, ge=512, le=32768)
    custom_template: Optional[str] = None
    ollama_parameters: Optional[Dict[str, Any]] = None
    
    personality_traits: Optional[Dict[str, Any]] = None
    conversation_style: str = Field(default="professional", pattern="^(professional|friendly|casual)$")
    response_time_limit: int = Field(default=30, ge=5, le=300)
    voice_id: Optional[str] = None
    voice_speed: float = Field(default=1.0, ge=0.5, le=2.0)
    voice_pitch: float = Field(default=1.0, ge=0.5, le=2.0)
    campaign_id: Optional[int] = None


class AgentUpdate(BaseModel):
    """Agent update schema"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|active|paused)$")
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None, ge=100, le=4000)
    system_prompt: Optional[str] = Field(None, min_length=10)
    
    # Ollama specific fields
    is_ollama_model: Optional[bool] = None
    ollama_model_name: Optional[str] = Field(None, min_length=2, max_length=100)
    base_model: Optional[str] = None
    num_ctx: Optional[int] = Field(None, ge=512, le=32768)
    custom_template: Optional[str] = None
    ollama_parameters: Optional[Dict[str, Any]] = None
    
    personality_traits: Optional[Dict[str, Any]] = None
    conversation_style: Optional[str] = Field(None, pattern="^(professional|friendly|casual)$")
    response_time_limit: Optional[int] = Field(None, ge=5, le=300)
    voice_id: Optional[str] = None
    voice_speed: Optional[float] = Field(None, ge=0.5, le=2.0)
    voice_pitch: Optional[float] = Field(None, ge=0.5, le=2.0)
    campaign_id: Optional[int] = None
    is_active: Optional[bool] = None


class AgentResponse(AgentBase):
    """Agent response schema"""
    id: int
    status: str
    is_active: bool
    model: str
    temperature: float
    max_tokens: int
    system_prompt: str
    
    # Ollama specific fields
    is_ollama_model: bool
    ollama_model_name: Optional[str]
    base_model: str
    num_ctx: int
    modelfile_content: Optional[str]
    custom_template: Optional[str]
    ollama_parameters: Optional[Dict[str, Any]]
    
    personality_traits: Optional[Dict[str, Any]]
    conversation_style: str
    response_time_limit: int
    voice_id: Optional[str]
    voice_speed: float
    voice_pitch: float
    total_interactions: int
    successful_interactions: int
    success_rate: float
    avg_interaction_duration: float
    avg_response_time: float
    total_cost: float
    training_data: Optional[Dict[str, Any]]
    feedback_score: float
    last_training_date: Optional[datetime]
    creator_id: int
    campaign_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    last_used: Optional[datetime]

    class Config:
        from_attributes = True


class AgentMetrics(BaseModel):
    """Agent metrics schema"""
    total_interactions: int
    successful_interactions: int
    success_rate: float
    avg_interaction_duration: float
    avg_response_time: float
    total_cost: float
    feedback_score: float


class AgentSummary(BaseModel):
    """Agent summary schema"""
    id: int
    name: str
    agent_type: str
    status: str
    success_rate: float
    total_interactions: int
    created_at: datetime

    class Config:
        from_attributes = True


class AgentTraining(BaseModel):
    """Agent training schema"""
    training_data: Dict[str, Any]
    feedback_score: Optional[float] = Field(None, ge=0.0, le=10.0)


class OllamaModelCreate(BaseModel):
    """Schema for creating Ollama models"""
    name: str = Field(..., min_length=2, max_length=100, description="Name for the custom Ollama model")
    base_model: str = Field(default="llama2", description="Base model to use (llama2, mistral, etc.)")
    system_prompt: str = Field(..., min_length=10, description="System message to guide the model's behavior")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Model temperature for creativity")
    num_ctx: int = Field(default=2048, ge=512, le=8192, description="Context window size")
    custom_template: Optional[str] = Field(None, description="Custom prompt template")


class OllamaModelResponse(BaseModel):
    """Response schema for Ollama model creation"""
    success: bool
    message: str
    agent_id: Optional[int] = None
    ollama_model_name: Optional[str] = None
    modelfile_content: Optional[str] = None