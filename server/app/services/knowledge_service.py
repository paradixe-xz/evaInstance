"""
Knowledge Base service for managing agent knowledge
"""
import os
import shutil
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.agent import Agent
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import get_embedding_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Service for managing agent knowledge base"""
    
    def __init__(self, db: Session):
        """Initialize knowledge service"""
        self.db = db
        self.document_processor = DocumentProcessor()
        self.knowledge_base_path = Path(settings.KNOWLEDGE_BASE_PATH)
        self.knowledge_base_path.mkdir(exist_ok=True)
        
    def get_agent_knowledge_path(self, agent_id: int) -> Path:
        """Get knowledge base path for specific agent"""
        agent_path = self.knowledge_base_path / f"agent_{agent_id}"
        agent_path.mkdir(exist_ok=True)
        return agent_path
    
    def generate_unique_filename(self, agent_id: int, original_filename: str) -> str:
        """Generate unique filename for storage"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(original_filename)
        return f"{timestamp}_{name}{ext}"
    
    async def upload_document(self, agent_id: int, file_path: str, 
                            original_filename: str, title: str = None, 
                            description: str = None) -> Dict[str, Any]:
        """Upload and process a document for an agent"""
        try:
            # Verify agent exists
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                return {"success": False, "error": f"Agent {agent_id} not found"}
            
            # Check if file type is supported
            if not self.document_processor.is_supported_file(original_filename):
                return {"success": False, "error": f"Unsupported file type: {original_filename}"}
            
            # Calculate file hash to check for duplicates
            file_hash = self.document_processor.calculate_file_hash(file_path)
            
            # Check if document already exists
            existing_doc = self.db.query(KnowledgeDocument).filter(
                and_(
                    KnowledgeDocument.agent_id == agent_id,
                    KnowledgeDocument.content_hash == file_hash
                )
            ).first()
            
            if existing_doc:
                return {
                    "success": False, 
                    "error": "Document already exists in knowledge base",
                    "existing_document_id": existing_doc.id
                }
            
            # Generate unique filename and copy file
            unique_filename = self.generate_unique_filename(agent_id, original_filename)
            agent_path = self.get_agent_knowledge_path(agent_id)
            destination_path = agent_path / unique_filename
            
            shutil.copy2(file_path, destination_path)
            
            # Get file info
            file_size = os.path.getsize(destination_path)
            file_type = self.document_processor.get_file_type(original_filename)
            
            # Create document record
            document = KnowledgeDocument(
                agent_id=agent_id,
                filename=unique_filename,
                original_filename=original_filename,
                file_path=str(destination_path),
                file_type=file_type,
                file_size=file_size,
                content_hash=file_hash,
                title=title,
                description=description,
                status="pending"
            )
            
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            
            # Process document asynchronously
            asyncio.create_task(self._process_document_async(document.id))
            
            return {
                "success": True,
                "message": "Document uploaded successfully and processing started",
                "document_id": document.id,
                "filename": original_filename,
                "file_size": file_size,
                "status": "pending"
            }
            
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_document_async(self, document_id: int):
        """Process document asynchronously"""
        try:
            # Get document
            document = self.db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == document_id
            ).first()
            
            if not document:
                logger.error(f"Document {document_id} not found for processing")
                return
            
            # Update status
            document.status = "processing"
            self.db.commit()
            
            # Process document
            result = self.document_processor.process_document(
                document.file_path, 
                document.original_filename
            )
            
            if not result["success"]:
                document.status = "failed"
                document.error_message = result["error"]
                self.db.commit()
                logger.error(f"Failed to process document {document_id}: {result['error']}")
                return
            
            # Update document with extracted info
            if not document.title and result.get("title"):
                document.title = result["title"]
            
            document.total_chunks = result["total_chunks"]
            document.total_tokens = result["total_tokens"]
            
            # Get embedding service
            embedding_service = await get_embedding_service()
            embedding_dimension = await embedding_service.get_embedding_dimension()
            
            # Create chunks with embeddings
            chunks_created = 0
            for chunk_data in result["chunks"]:
                # Generate embedding for chunk
                embedding = await embedding_service.generate_embedding(chunk_data["content"])
                
                # Create chunk record
                chunk = KnowledgeChunk(
                    document_id=document.id,
                    chunk_index=chunk_data["chunk_index"],
                    content=chunk_data["content"],
                    content_hash=self.document_processor.calculate_file_hash(
                        chunk_data["content"].encode()
                    ),
                    token_count=chunk_data["token_count"],
                    start_char=chunk_data.get("start_char"),
                    end_char=chunk_data.get("end_char"),
                    page_number=chunk_data.get("page_number"),
                    embedding_model=embedding_service.model_name,
                    embedding_vector=embedding,
                    embedding_dimension=embedding_dimension,
                    chunk_metadata=chunk_data.get("metadata", {})
                )
                
                self.db.add(chunk)
                chunks_created += 1
            
            # Update document status
            document.status = "completed"
            document.processed_at = datetime.utcnow()
            document.total_chunks = chunks_created
            
            self.db.commit()
            
            logger.info(f"Successfully processed document {document_id} with {chunks_created} chunks")
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            
            # Update document with error
            document = self.db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == document_id
            ).first()
            
            if document:
                document.status = "failed"
                document.error_message = str(e)
                self.db.commit()
    
    def get_agent_documents(self, agent_id: int, skip: int = 0, limit: int = 100) -> List[KnowledgeDocument]:
        """Get all documents for an agent"""
        return self.db.query(KnowledgeDocument).filter(
            KnowledgeDocument.agent_id == agent_id
        ).order_by(desc(KnowledgeDocument.created_at)).offset(skip).limit(limit).all()
    
    def get_document(self, document_id: int, agent_id: int = None) -> Optional[KnowledgeDocument]:
        """Get a specific document"""
        query = self.db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id)
        
        if agent_id:
            query = query.filter(KnowledgeDocument.agent_id == agent_id)
        
        return query.first()
    
    def delete_document(self, document_id: int, agent_id: int = None) -> Dict[str, Any]:
        """Delete a document and its chunks"""
        try:
            # Get document
            document = self.get_document(document_id, agent_id)
            if not document:
                return {"success": False, "error": "Document not found"}
            
            # Delete file from filesystem
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            # Delete chunks (cascade should handle this, but being explicit)
            self.db.query(KnowledgeChunk).filter(
                KnowledgeChunk.document_id == document_id
            ).delete()
            
            # Delete document
            self.db.delete(document)
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Document {document.original_filename} deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def search_knowledge(self, agent_id: int, query: str, 
                             limit: int = 5, threshold: float = 0.7) -> Dict[str, Any]:
        """Search agent's knowledge base"""
        try:
            start_time = datetime.now()
            
            # Get all chunks for the agent
            chunks = self.db.query(KnowledgeChunk).join(KnowledgeDocument).filter(
                and_(
                    KnowledgeDocument.agent_id == agent_id,
                    KnowledgeDocument.status == "completed",
                    KnowledgeChunk.embedding_vector.isnot(None)
                )
            ).all()
            
            if not chunks:
                return {
                    "query": query,
                    "results": [],
                    "total_results": 0,
                    "search_time_ms": 0
                }
            
            # Get embedding service and search
            embedding_service = await get_embedding_service()
            
            # Prepare chunk embeddings
            chunk_embeddings = [
                (chunk.id, chunk.embedding_vector) 
                for chunk in chunks 
                if chunk.embedding_vector
            ]
            
            # Search for similar chunks
            similar_chunks = await embedding_service.search_similar_chunks(
                query, chunk_embeddings, limit, threshold
            )
            
            # Get full chunk data
            results = []
            for chunk_id, similarity_score in similar_chunks:
                chunk = next((c for c in chunks if c.id == chunk_id), None)
                if chunk:
                    result = {
                        "id": chunk.id,
                        "document_id": chunk.document_id,
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.content,
                        "token_count": chunk.token_count,
                        "similarity_score": similarity_score,
                        "document_filename": chunk.document.original_filename,
                        "document_title": chunk.document.title,
                        "page_number": chunk.page_number,
                        "metadata": chunk.chunk_metadata
                    }
                    results.append(result)
            
            search_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "query": query,
                "results": results,
                "total_results": len(results),
                "search_time_ms": search_time
            }
            
        except Exception as e:
            logger.error(f"Error searching knowledge for agent {agent_id}: {e}")
            return {
                "query": query,
                "results": [],
                "total_results": 0,
                "search_time_ms": 0,
                "error": str(e)
            }
    
    def get_knowledge_stats(self, agent_id: int) -> Dict[str, Any]:
        """Get knowledge base statistics for an agent"""
        try:
            documents = self.db.query(KnowledgeDocument).filter(
                KnowledgeDocument.agent_id == agent_id
            ).all()
            
            if not documents:
                return {
                    "agent_id": agent_id,
                    "total_documents": 0,
                    "total_chunks": 0,
                    "total_tokens": 0,
                    "total_size_bytes": 0,
                    "documents_by_type": {},
                    "processing_status": {},
                    "last_updated": None
                }
            
            # Calculate statistics
            total_documents = len(documents)
            total_chunks = sum(doc.total_chunks for doc in documents)
            total_tokens = sum(doc.total_tokens for doc in documents)
            total_size_bytes = sum(doc.file_size for doc in documents)
            
            # Group by file type
            documents_by_type = {}
            for doc in documents:
                documents_by_type[doc.file_type] = documents_by_type.get(doc.file_type, 0) + 1
            
            # Group by status
            processing_status = {}
            for doc in documents:
                processing_status[doc.status] = processing_status.get(doc.status, 0) + 1
            
            # Get last updated
            last_updated = max(doc.updated_at for doc in documents) if documents else None
            
            return {
                "agent_id": agent_id,
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "total_tokens": total_tokens,
                "total_size_bytes": total_size_bytes,
                "documents_by_type": documents_by_type,
                "processing_status": processing_status,
                "last_updated": last_updated
            }
            
        except Exception as e:
            logger.error(f"Error getting knowledge stats for agent {agent_id}: {e}")
            return {"error": str(e)}
    
    async def reindex_document(self, document_id: int) -> Dict[str, Any]:
        """Reindex a document (regenerate embeddings)"""
        try:
            document = self.db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == document_id
            ).first()
            
            if not document:
                return {"success": False, "error": "Document not found"}
            
            # Delete existing chunks
            self.db.query(KnowledgeChunk).filter(
                KnowledgeChunk.document_id == document_id
            ).delete()
            
            # Reset document status
            document.status = "pending"
            document.processed_at = None
            document.error_message = None
            self.db.commit()
            
            # Reprocess document
            asyncio.create_task(self._process_document_async(document_id))
            
            return {
                "success": True,
                "message": "Document reindexing started",
                "document_id": document_id
            }
            
        except Exception as e:
            logger.error(f"Error reindexing document {document_id}: {e}")
            return {"success": False, "error": str(e)}

    # Factory function for creating a KnowledgeService with a DB session

def get_knowledge_service(db: Session) -> KnowledgeService:
    return KnowledgeService(db)