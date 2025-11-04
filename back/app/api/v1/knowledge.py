"""
Knowledge Base API endpoints
"""

import os
import tempfile
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_max_file_size_bytes
from app.schemas.knowledge import (
    KnowledgeDocumentResponse,
    KnowledgeSearchRequest,
    KnowledgeStats,
)
from app.services.knowledge_service import get_knowledge_service
from app.models.agent import Agent

router = APIRouter()


@router.post("/agents/{agent_id}/knowledge/upload")
async def upload_knowledge_document(
    agent_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload a knowledge document for an agent
    """
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Verify file type
    allowed_types = ['.pdf', '.txt', '.docx', '.md', '.json']
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed types: {', '.join(allowed_types)}"
        )
    
    try:
        # Persist upload to a temporary path
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        service = get_knowledge_service(db)
        result = await service.upload_document(
            agent_id=agent_id,
            file_path=tmp_path,
            original_filename=file.filename,
            title=None,
            description=description
        )
        
        # Cleanup temporary file
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=f"Upload failed: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/agents/{agent_id}/knowledge")
async def list_knowledge_documents(
    agent_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[KnowledgeDocumentResponse]:
    """
    List all knowledge documents for an agent
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    service = get_knowledge_service(db)
    documents = service.get_agent_documents(
        agent_id=agent_id,
        skip=skip,
        limit=limit
    )
    
    return documents


@router.get("/agents/{agent_id}/knowledge/{document_id}")
async def get_knowledge_document(
    agent_id: int,
    document_id: int,
    db: Session = Depends(get_db)
) -> KnowledgeDocumentResponse:
    """
    Get a specific knowledge document
    """
    service = get_knowledge_service(db)
    document = service.get_document(
        document_id=document_id,
        agent_id=agent_id
    )
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.delete("/agents/{agent_id}/knowledge/{document_id}")
async def delete_knowledge_document(
    agent_id: int,
    document_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete a knowledge document
    """
    service = get_knowledge_service(db)
    result = service.delete_document(
        document_id=document_id,
        agent_id=agent_id
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Document not found"))
    
    return {"message": result.get("message", "Document deleted successfully")}


@router.post("/agents/{agent_id}/knowledge/search")
async def search_knowledge(
    agent_id: int,
    search_request: KnowledgeSearchRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Search knowledge base for relevant content
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        service = get_knowledge_service(db)
        search_data = await service.search_knowledge(
            agent_id=agent_id,
            query=search_request.query,
            limit=search_request.limit,
            threshold=search_request.similarity_threshold
        )
        return search_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/agents/{agent_id}/knowledge/reindex")
async def reindex_knowledge(
    agent_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reindex all knowledge documents for an agent
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    service = get_knowledge_service(db)
    documents = service.get_agent_documents(agent_id=agent_id, skip=0, limit=100)
    
    # Schedule reindexing for each document
    for doc in documents:
        background_tasks.add_task(service.reindex_document, doc.id)
    
    return {"message": "Reindexing started", "documents": [doc.id for doc in documents]}


@router.get("/agents/{agent_id}/knowledge/status/{document_id}")
async def get_processing_status(
    agent_id: int,
    document_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get processing status of a document
    """
    service = get_knowledge_service(db)
    document = service.get_document(
        document_id=document_id,
        agent_id=agent_id
    )
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    status = document.status
    progress = 100.0 if status == "completed" else 0.0
    
    return {
        "document_id": document.id,
        "filename": document.filename,
        "status": status,
        "progress_percentage": progress,
        "chunks_processed": document.total_chunks or 0,
        "total_chunks": document.total_chunks or 0,
        "error_message": document.error_message,
        "estimated_completion": None
    }


@router.get("/agents/{agent_id}/knowledge/stats")
async def get_knowledge_statistics(
    agent_id: int,
    db: Session = Depends(get_db)
) -> KnowledgeStats:
    """
    Get knowledge base statistics for an agent
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    service = get_knowledge_service(db)
    stats = service.get_knowledge_stats(agent_id=agent_id)
    return stats


@router.post("/agents/{agent_id}/knowledge/rag")
async def rag_query(
    agent_id: int,
    search_request: KnowledgeSearchRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Perform a simple RAG (Retrieval-Augmented Generation) query
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        service = get_knowledge_service(db)
        search_data = await service.search_knowledge(
            agent_id=agent_id,
            query=search_request.query,
            limit=search_request.limit,
            threshold=search_request.similarity_threshold
        )
        
        results = search_data.get("results", [])
        context = "\n\n".join([r.get("content", "") for r in results])
        
        return {
            "response": "",
            "sources": results,
            "search_query": search_request.query,
            "total_sources": len(results),
            "search_time_ms": search_data.get("search_time_ms", 0.0),
            "generation_time_ms": 0.0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")