"""
API endpoints for managing conversation flows
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
import json
from pathlib import Path

from ....core.config import get_settings
from ....services.conversation_service import ConversationService
from ....schemas.conversation_flow import FlowCreate, FlowUpdate, FlowResponse

router = APIRouter()
settings = get_settings()

# Initialize conversation service
conversation_service = ConversationService()

@router.get("/flows", response_model=List[str])
async def list_flows():
    """List all available conversation flows"""
    try:
        return conversation_service.list_available_flows()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing flows: {str(e)}"
        )

@router.get("/flows/{flow_name}", response_model=Dict[str, Any])
async def get_flow(flow_name: str):
    """Get a specific conversation flow"""
    try:
        return conversation_service.load_flow_from_file(flow_name)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flow '{flow_name}' not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading flow: {str(e)}"
        )

@router.post("/flows", response_model=Dict[str, str], status_code=status.HTTP_201_CREATED)
async def create_flow(flow_data: FlowCreate):
    """Create a new conversation flow"""
    try:
        file_path = conversation_service.save_flow_to_file(
            flow_name=flow_data.name,
            flow_data=flow_data.flow
        )
        return {"message": "Flow created successfully", "file_path": file_path}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating flow: {str(e)}"
        )

@router.put("/flows/{flow_name}", response_model=Dict[str, str])
async def update_flow(flow_name: str, flow_data: FlowUpdate):
    """Update an existing conversation flow"""
    try:
        # First check if flow exists
        conversation_service.load_flow_from_file(flow_name)
        
        # Save updated flow
        file_path = conversation_service.save_flow_to_file(
            flow_name=flow_name,
            flow_data=flow_data.flow
        )
        return {"message": "Flow updated successfully", "file_path": file_path}
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flow '{flow_name}' not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating flow: {str(e)}"
        )

@router.delete("/flows/{flow_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flow(flow_name: str):
    """Delete a conversation flow"""
    try:
        file_path = Path(f"conversation_flows/{flow_name}.json")
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow '{flow_name}' not found"
            )
        file_path.unlink()
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting flow: {str(e)}"
        )
