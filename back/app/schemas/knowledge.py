"""
Pydantic schemas for Knowledge Base
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class KnowledgeDocumentBase(BaseModel):
    """Base schema for knowledge documents"""
    filename: str = Field(..., description="Document filename")
    title: Optional[str] = Field(None, description="Document title")
    description: Optional[str] = Field(None, description="Document description")
    language: str = Field("es", description="Document language")


class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    """Schema for creating knowledge documents"""
    pass


class KnowledgeDocumentUpdate(BaseModel):
    """Schema for updating knowledge documents"""
    title: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None


class KnowledgeDocumentResponse(KnowledgeDocumentBase):
    """Schema for knowledge document responses"""
    id: int
    agent_id: int
    original_filename: str
    file_type: str
    file_size: int
    status: str
    processed_at: Optional[datetime]
    error_message: Optional[str]
    total_chunks: int
    total_tokens: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class KnowledgeChunkBase(BaseModel):
    """Base schema for knowledge chunks"""
    content: str = Field(..., description="Chunk content")
    chunk_index: int = Field(..., description="Chunk order in document")
    token_count: int = Field(..., description="Number of tokens in chunk")


class KnowledgeChunkCreate(KnowledgeChunkBase):
    """Schema for creating knowledge chunks"""
    document_id: int
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    page_number: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeChunkResponse(KnowledgeChunkBase):
    """Schema for knowledge chunk responses"""
    id: int
    document_id: int
    content_hash: str
    start_char: Optional[int]
    end_char: Optional[int]
    page_number: Optional[int]
    embedding_model: Optional[str]
    embedding_dimension: Optional[int]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class KnowledgeChunkWithSimilarity(KnowledgeChunkResponse):
    """Schema for knowledge chunk with similarity score"""
    similarity_score: float = Field(..., description="Similarity score to query")
    document_filename: str = Field(..., description="Source document filename")


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response"""
    success: bool
    message: str
    document_id: Optional[int] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    status: Optional[str] = None


class KnowledgeSearchRequest(BaseModel):
    """Schema for knowledge search requests"""
    query: str = Field(..., description="Search query")
    agent_id: int = Field(..., description="Agent ID to search knowledge for")
    limit: int = Field(5, description="Maximum number of results", ge=1, le=20)
    similarity_threshold: float = Field(0.7, description="Minimum similarity score", ge=0.0, le=1.0)


class KnowledgeSearchResponse(BaseModel):
    """Schema for knowledge search responses"""
    query: str
    results: List[KnowledgeChunkWithSimilarity]
    total_results: int
    search_time_ms: float


class DocumentProcessingStatus(BaseModel):
    """Schema for document processing status"""
    document_id: int
    filename: str
    status: str
    progress_percentage: float
    chunks_processed: int
    total_chunks: int
    error_message: Optional[str] = None
    estimated_completion: Optional[datetime] = None


class KnowledgeStats(BaseModel):
    """Schema for knowledge base statistics"""
    agent_id: int
    total_documents: int
    total_chunks: int
    total_tokens: int
    total_size_bytes: int
    documents_by_type: Dict[str, int]
    processing_status: Dict[str, int]  # status -> count
    last_updated: Optional[datetime]


class RAGResponse(BaseModel):
    """Schema for RAG (Retrieval-Augmented Generation) responses"""
    response: str = Field(..., description="Generated response")
    sources: List[KnowledgeChunkWithSimilarity] = Field(..., description="Source chunks used")
    confidence_score: float = Field(..., description="Response confidence", ge=0.0, le=1.0)
    tokens_used: int = Field(..., description="Tokens used in generation")
    search_time_ms: float = Field(..., description="Time spent searching knowledge")
    generation_time_ms: float = Field(..., description="Time spent generating response")