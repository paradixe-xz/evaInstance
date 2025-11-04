"""
AI Agent management endpoints.
"""
from typing import List, Optional, Dict
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models import Agent, SystemUser, Campaign
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentSummary,
    AgentMetrics,
    AgentTraining,
    OllamaModelCreate,
    OllamaModelResponse
)
from app.core.dependencies import get_current_user
from app.services.agent_service import AgentService
from app.core.exceptions import AgentError, OllamaError

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None


@router.get("/", response_model=List[AgentSummary])
async def get_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    agent_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    campaign_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Get all agents for the current user."""
    query = db.query(Agent).filter(Agent.creator_id == current_user.id)
    
    if agent_type:
        query = query.filter(Agent.agent_type == agent_type)
    if status:
        query = query.filter(Agent.status == status)
    if campaign_id:
        query = query.filter(Agent.campaign_id == campaign_id)
    
    agents = query.offset(skip).limit(limit).all()
    return agents


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent: AgentCreate,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Create a new AI agent."""
    try:
        agent_service = AgentService(db)
        created_agent = agent_service.create_agent(agent, current_user.id)
        return created_agent
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Get a specific agent by ID."""
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.creator_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_update: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Update an agent."""
    try:
        agent_service = AgentService(db)
        
        # Check if agent exists and belongs to user
        agent = agent_service.get_agent_by_id(agent_id)
        if not agent or agent.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        updated_agent = agent_service.update_agent(agent_id, agent_update)
        if not updated_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        return updated_agent
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Delete an agent."""
    try:
        agent_service = AgentService(db)
        
        # Check if agent exists and belongs to user
        agent = agent_service.get_agent_by_id(agent_id)
        if not agent or agent.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        success = agent_service.delete_agent(agent_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
            
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{agent_id}/metrics", response_model=AgentMetrics)
async def get_agent_metrics(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Get agent performance metrics."""
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.creator_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Calculate metrics from agent data
    metrics = AgentMetrics(
        total_calls=agent.total_calls,
        total_messages=agent.total_messages,
        success_rate=agent.calculate_success_rate(),
        average_response_time=agent.average_response_time,
        total_cost=agent.total_cost,
        uptime_percentage=agent.uptime_percentage,
        last_active=agent.last_used
    )
    
    return metrics


@router.post("/{agent_id}/activate")
async def activate_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Activate an agent."""
    try:
        agent_service = AgentService(db)
        
        # Check if agent exists and belongs to user
        agent = agent_service.get_agent_by_id(agent_id)
        if not agent or agent.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        if agent.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent is already active"
            )
        
        success = agent_service.activate_agent(agent_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to activate agent"
            )
        
        return {"message": "Agent activated successfully"}
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{agent_id}/deactivate")
async def deactivate_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Deactivate an agent."""
    try:
        agent_service = AgentService(db)
        
        # Check if agent exists and belongs to user
        agent = agent_service.get_agent_by_id(agent_id)
        if not agent or agent.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        if not agent.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent is not active"
            )
        
        success = agent_service.deactivate_agent(agent_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to deactivate agent"
            )
        
        return {"message": "Agent deactivated successfully"}
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{agent_id}/train", response_model=AgentResponse)
async def train_agent(
    agent_id: int,
    training_data: AgentTraining,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Train an agent with new data."""
    try:
        agent_service = AgentService(db)
        
        # Check if agent exists and belongs to user
        agent = agent_service.get_agent_by_id(agent_id)
        if not agent or agent.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        # Prepare update data
        update_data = {}
        if training_data.training_examples:
            update_data["training_data"] = training_data.training_examples
        
        if training_data.system_prompt:
            update_data["system_prompt"] = training_data.system_prompt
        
        if training_data.personality_traits:
            update_data["personality_traits"] = training_data.personality_traits
        
        # Mark as training
        update_data["status"] = "training"
        
        updated_agent = agent_service.update_agent(agent_id, update_data)
        if not updated_agent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update agent training data"
            )
        
        # Here you would typically trigger the actual training process
        # For now, we'll just mark it as trained
        final_update = {"status": "active"}
        final_agent = agent_service.update_agent(agent_id, final_update)
        
        return final_agent
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{agent_id}/test")
async def test_agent(
    agent_id: int,
    message: str = Query(..., description="Test message to send to the agent"),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Test an agent with a sample message."""
    try:
        agent_service = AgentService(db)
        agent = agent_service.get_agent_by_id(agent_id)
        
        if not agent or agent.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        if not agent.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent must be active to test"
            )
        
        # Use the agent service to test the agent
        response = agent_service.test_agent(agent_id, message)
        
        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "test_message": message,
            "agent_response": response,
            "success": True
        }
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except OllamaError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# Ollama-specific endpoints

@router.post("/ollama/create", status_code=status.HTTP_201_CREATED)
async def create_ollama_model(
    model_data: OllamaModelCreate,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Create a custom Ollama model."""
    try:
        agent_service = AgentService(db)
        result = agent_service.create_ollama_model(model_data, current_user.id)
        
        return {
            "success": result["success"],
            "model_name": result["model_name"],
            "base_model": result["base_model"],
            "temperature": result["temperature"],
            "num_ctx": result["num_ctx"],
            "system_prompt": result["system_prompt"],
            "custom_template": result["custom_template"],
            "message": result["message"]
        }
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except OllamaError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Ollama model: {str(e)}"
        )


@router.put("/ollama/{agent_id}")
async def update_ollama_model(
    agent_id: int,
    model_data: OllamaModelCreate,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Update an existing Ollama model."""
    try:
        agent_service = AgentService(db)
        
        # Verify the agent exists and belongs to the current user
        agent = agent_service.get_agent_by_id(agent_id)
        if not agent or agent.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        if not agent.is_ollama_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent is not an Ollama model"
            )
        
        result = agent_service.update_ollama_model(agent_id, model_data, current_user.id)
        
        return {
            "success": result["success"],
            "agent_id": agent_id,
            "model_name": result["model_name"],
            "base_model": result["base_model"],
            "temperature": result["temperature"],
            "num_ctx": result["num_ctx"],
            "system_prompt": result["system_prompt"],
            "custom_template": result["custom_template"],
            "message": result["message"]
        }
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except OllamaError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update Ollama model: {str(e)}"
        )


@router.get("/ollama/base-models")
async def get_available_base_models(
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Get list of available base models for Ollama."""
    try:
        agent_service = AgentService(db)
        models = agent_service.get_available_base_models()
        
        return {
            "success": True,
            "base_models": models,
            "count": len(models)
        }
        
    except OllamaError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get base models: {str(e)}"
        )


@router.get("/ollama/models")
async def get_ollama_models(
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Get Ollama models created by the current user."""
    try:
        agent_service = AgentService(db)
        agents = agent_service.get_ollama_agents(current_user.id)
        
        # Convert agents to model format
        models = []
        for agent in agents:
            models.append({
                "id": agent.id,
                "name": agent.ollama_model_name,
                "display_name": agent.name,
                "base_model": agent.base_model,
                "size": "Unknown",  # We don't track size in our DB
                "modified_at": agent.updated_at.isoformat() if agent.updated_at else None,
                "digest": "Unknown",  # We don't track digest in our DB
                "system_prompt": agent.system_prompt,
                "temperature": agent.temperature,
                "num_ctx": agent.num_ctx,
                "custom_template": agent.custom_template,
                "modelfile_content": agent.modelfile_content,
                "created_at": agent.created_at.isoformat() if agent.created_at else None,
                "status": agent.status
            })
        
        return {
            "success": True,
            "models": models,
            "count": len(models)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user Ollama models: {str(e)}"
        )


@router.get("/{agent_id}/modelfile")
async def get_agent_modelfile(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Get the modelfile content for an Ollama agent."""
    try:
        agent_service = AgentService(db)
        agent = agent_service.get_agent_by_id(agent_id)
        
        if not agent or agent.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        if not agent.is_ollama_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent is not an Ollama model"
            )
        
        return {
            "success": True,
            "agent_id": agent_id,
            "agent_name": agent.name,
            "ollama_model_name": agent.ollama_model_name,
            "modelfile_content": agent.modelfile_content,
            "base_model": agent.base_model
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get modelfile: {str(e)}"
        )


@router.post("/ollama/{agent_id}/chat")
async def chat_with_ollama_model(
    agent_id: int,
    message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Chat with an Ollama model."""
    try:
        agent_service = AgentService(db)
        agent = agent_service.get_agent_by_id(agent_id)
        
        if not agent or agent.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        if not agent.is_ollama_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent is not an Ollama model"
            )
        
        # Generate response using the agent's Ollama model
        response = agent_service.chat_with_ollama_model(
            agent_id=agent_id,
            message=message,
            conversation_history=conversation_history or []
        )
        
        return {
            "success": True,
            "agent_id": agent_id,
            "agent_name": agent.name,
            "model_name": agent.ollama_model_name,
            "user_message": message,
            "ai_response": response,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except OllamaError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to chat with model: {str(e)}"
        )


@router.post("/ollama/{agent_id}/chat/knowledge")
async def chat_with_knowledge_base(
    agent_id: int,
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Chat with an Ollama model enhanced with Knowledge Base (RAG)."""
    try:
        agent_service = AgentService(db)
        agent = agent_service.get_agent_by_id(agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        if not agent.is_ollama_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent is not an Ollama model"
            )
        
        # Generate response using the agent's Ollama model with Knowledge Base
        response_data = await agent_service.chat_with_knowledge_base(
            agent_id=agent_id,
            message=chat_request.message,
            conversation_history=chat_request.conversation_history or [],
            db=db
        )
        
        return {
            "success": True,
            "agent_id": agent_id,
            "agent_name": agent.name,
            "model_name": agent.ollama_model_name,
            "user_message": chat_request.message,
            "ai_response": response_data["ai_response"],
            "knowledge_used": response_data["knowledge_used"],
            "sources": response_data["sources"],
            "knowledge_count": response_data["knowledge_count"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except OllamaError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to chat with model: {str(e)}"
        )


@router.post("/ollama/{agent_id}/chat/test")
async def test_chat_with_ollama_model(
    agent_id: int,
    message: str = Query(..., description="Message to send to the model"),
    db: Session = Depends(get_db)
):
    """Test chat with an Ollama model without authentication."""
    try:
        agent_service = AgentService(db)
        agent = agent_service.get_agent_by_id(agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        if not agent.is_ollama_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent is not an Ollama model"
            )
        
        # Generate response using the agent's Ollama model
        response = agent_service.chat_with_ollama_model(
            agent_id=agent_id,
            message=message,
            conversation_history=[]
        )
        
        return {
            "success": True,
            "agent_id": agent_id,
            "agent_name": agent.name,
            "model_name": agent.ollama_model_name,
            "user_message": message,
            "ai_response": response,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except OllamaError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to chat with model: {str(e)}"
        )


@router.post("/ollama/{agent_id}/chat/public")
async def public_chat_with_ollama_model(
    agent_id: int,
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Public chat endpoint with real Ollama model (no authentication required)."""
    try:
        agent_service = AgentService(db)
        agent = agent_service.get_agent_by_id(agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        if not agent.is_ollama_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent is not an Ollama model"
            )
        
        # Generate response using the agent's Ollama model
        response = agent_service.chat_with_ollama_model(
            agent_id=agent_id,
            message=chat_request.message,
            conversation_history=chat_request.conversation_history or []
        )
        
        return {
            "success": True,
            "agent_id": agent_id,
            "agent_name": agent.name,
            "model_name": agent.ollama_model_name,
            "user_message": chat_request.message,
            "ai_response": response,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except AgentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except OllamaError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to chat with model: {str(e)}"
        )