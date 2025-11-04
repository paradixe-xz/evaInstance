"""
Knowledge Document model for storing agent knowledge base files
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class KnowledgeDocument(Base):
    """Model for knowledge base documents"""
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, txt, docx, md, json
    file_size = Column(Integer, nullable=False)  # in bytes
    content_hash = Column(String(64), nullable=False, unique=True)  # SHA-256 hash
    
    # Processing status
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    title = Column(String(500), nullable=True)  # extracted or provided title
    description = Column(Text, nullable=True)
    language = Column(String(10), default="es")
    total_chunks = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    agent = relationship("Agent", back_populates="knowledge_documents")
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KnowledgeDocument(id={self.id}, filename='{self.filename}', agent_id={self.agent_id})>"
    
    def to_dict(self):
        """Convert document to dictionary"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "status": self.status,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "error_message": self.error_message,
            "title": self.title,
            "description": self.description,
            "language": self.language,
            "total_chunks": self.total_chunks,
            "total_tokens": self.total_tokens,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }