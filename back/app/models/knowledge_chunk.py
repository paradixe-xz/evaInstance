"""
Knowledge Chunk model for storing document chunks with embeddings
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class KnowledgeChunk(Base):
    """Model for knowledge base document chunks"""
    __tablename__ = "knowledge_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)  # Order within document
    
    # Content
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)  # SHA-256 hash of content
    token_count = Column(Integer, nullable=False)
    
    # Position in document
    start_char = Column(Integer, nullable=True)  # Character position in original document
    end_char = Column(Integer, nullable=True)
    page_number = Column(Integer, nullable=True)  # For PDFs
    
    # Embedding data
    embedding_model = Column(String(100), nullable=True)  # e.g., "nomic-embed-text"
    embedding_vector = Column(JSON, nullable=True)  # Store as JSON array
    embedding_dimension = Column(Integer, nullable=True)
    
    # Metadata
    chunk_metadata = Column(JSON, nullable=True)  # Additional chunk metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("KnowledgeDocument", back_populates="chunks")
    
    def __repr__(self):
        return f"<KnowledgeChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"
    
    def to_dict(self, include_embedding=False):
        """Convert chunk to dictionary"""
        data = {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "token_count": self.token_count,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "page_number": self.page_number,
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.embedding_dimension,
            "metadata": self.chunk_metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
        
        if include_embedding and self.embedding_vector:
            data["embedding_vector"] = self.embedding_vector
            
        return data
    
    def get_similarity_score(self, query_embedding):
        """Calculate cosine similarity with query embedding"""
        if not self.embedding_vector or not query_embedding:
            return 0.0
            
        # Simple dot product for normalized vectors
        # In production, you might want to use numpy or specialized libraries
        if len(self.embedding_vector) != len(query_embedding):
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(self.embedding_vector, query_embedding))
        return dot_product