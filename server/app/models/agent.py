"""
Agent model for Eva AI agents
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship

from ..core.database import Base


class Agent(Base):
    """Agent model for Eva AI agents"""
    
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Agent type and status
    agent_type = Column(String(20), nullable=False)  # calls, whatsapp
    status = Column(String(20), default="draft")  # draft, active, paused
    is_active = Column(Boolean, default=True)
    
    # AI Configuration
    model = Column(String(50), default="gpt-4")  # gpt-4, gpt-3.5-turbo, claude-3, ollama models, etc.
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)
    system_prompt = Column(Text, nullable=False)
    
    # Ollama specific configuration
    is_ollama_model = Column(Boolean, default=False)
    ollama_model_name = Column(String(100), nullable=True)  # Custom model name in Ollama
    base_model = Column(String(50), default="llama3")  # Base model for Ollama (llama3, mistral, etc.)
    num_ctx = Column(Integer, default=4096)  # Context window size for Ollama
    modelfile_content = Column(Text, nullable=True)  # Complete Modelfile content
    custom_template = Column(Text, nullable=True)  # Custom prompt template
    ollama_parameters = Column(JSON, nullable=True)  # Additional Ollama parameters
    
    # Agent behavior configuration
    personality_traits = Column(JSON, nullable=True)  # JSON object with traits
    conversation_style = Column(String(50), default="professional")  # professional, friendly, casual
    response_time_limit = Column(Integer, default=30)  # seconds
    workflow_steps = Column(JSON, nullable=True)  # Ordered checklist for the agent
    conversation_structure = Column(JSON, nullable=True)  # Detailed step-by-step structure
    
    # Voice settings (for call agents)
    voice_id = Column(String(100), nullable=True)
    voice_speed = Column(Float, default=1.0)
    voice_pitch = Column(Float, default=1.0)
    
    # Performance metrics
    total_interactions = Column(Integer, default=0)
    successful_interactions = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_interaction_duration = Column(Float, default=0.0)  # in seconds
    avg_response_time = Column(Float, default=0.0)  # in seconds
    total_cost = Column(Float, default=0.0)
    
    # Training and improvement
    training_data = Column(JSON, nullable=True)  # JSON with training examples
    feedback_score = Column(Float, default=0.0)
    last_training_date = Column(DateTime, nullable=True)
    
    # Ownership and campaign
    creator_id = Column(Integer, ForeignKey("system_users.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    
    # Relationships
    creator = relationship("SystemUser", back_populates="agents")
    campaign = relationship("Campaign", back_populates="agents")
    call_logs = relationship("CallLog", back_populates="agent", cascade="all, delete-orphan")
    knowledge_documents = relationship("KnowledgeDocument", back_populates="agent", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}', type='{self.agent_type}')>"
    
    def calculate_success_rate(self):
        """Calculate and update success rate"""
        if self.total_interactions > 0:
            self.success_rate = (self.successful_interactions / self.total_interactions) * 100
        else:
            self.success_rate = 0.0
    
    def update_last_used(self):
        """Update last used timestamp"""
        self.last_used = datetime.utcnow()
    
    def to_dict(self):
        """Convert agent to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type,
            "status": self.status,
            "is_active": self.is_active,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "system_prompt": self.system_prompt,
            "is_ollama_model": self.is_ollama_model,
            "ollama_model_name": self.ollama_model_name,
            "base_model": self.base_model,
            "num_ctx": self.num_ctx,
            "modelfile_content": self.modelfile_content,
            "custom_template": self.custom_template,
            "ollama_parameters": self.ollama_parameters,
            "personality_traits": self.personality_traits,
            "conversation_style": self.conversation_style,
            "response_time_limit": self.response_time_limit,
            "workflow_steps": self.workflow_steps,
            "conversation_structure": self.conversation_structure,
            "voice_id": self.voice_id,
            "voice_speed": self.voice_speed,
            "voice_pitch": self.voice_pitch,
            "total_interactions": self.total_interactions,
            "successful_interactions": self.successful_interactions,
            "success_rate": self.success_rate,
            "avg_interaction_duration": self.avg_interaction_duration,
            "avg_response_time": self.avg_response_time,
            "total_cost": self.total_cost,
            "training_data": self.training_data,
            "feedback_score": self.feedback_score,
            "last_training_date": self.last_training_date.isoformat() if self.last_training_date else None,
            "creator_id": self.creator_id,
            "campaign_id": self.campaign_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None
        }