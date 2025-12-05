"""
RAG (Retrieval-Augmented Generation) Service
Integrates Knowledge Base with chat functionality
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.services.knowledge_service import get_knowledge_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """Service for Retrieval-Augmented Generation"""
    
    def __init__(self):
        self.similarity_threshold = settings.similarity_threshold
        self.max_search_results = settings.max_search_results
    
    async def enhance_prompt_with_knowledge(
        self,
        agent_id: int,
        user_message: str,
        db: Session,
        max_context_length: int = 2000
    ) -> Dict[str, Any]:
        """
        Enhance user prompt with relevant knowledge from the agent's knowledge base
        
        Args:
            agent_id: ID of the agent
            user_message: User's message/query
            db: Database session
            max_context_length: Maximum length of context to include
            
        Returns:
            Dict containing enhanced prompt, context, and sources
        """
        try:
            # Buscar conocimiento relevante
            service = get_knowledge_service(db)
            search_data = await service.search_knowledge(
                agent_id=agent_id,
                query=user_message,
                limit=self.max_search_results,
                threshold=self.similarity_threshold
            )
            results_list = search_data.get("results", [])
            
            if not results_list:
                return {
                    "enhanced_prompt": user_message,
                    "context": "",
                    "sources": [],
                    "has_knowledge": False
                }
            
            # Construir contexto desde los resultados
            context_chunks = []
            sources = []
            total_length = 0
            
            for result in results_list:
                chunk_text = f"[From {result['document_filename']}]: {result['content']}"
                
                # Verificar si agregar este chunk excede el límite
                if total_length + len(chunk_text) > max_context_length:
                    break
                
                context_chunks.append(chunk_text)
                sources.append({
                    "document_id": result["document_id"],
                    "filename": result["document_filename"],
                    "chunk_index": result["chunk_index"],
                    "similarity_score": result["similarity_score"],
                    "content_preview": (result["content"][:100] + "..." if len(result["content"]) > 100 else result["content"]) 
                })
                total_length += len(chunk_text)
            
            context = "\n\n".join(context_chunks)
            
            # Construir prompt mejorado
            enhanced_prompt = self._build_enhanced_prompt(user_message, context)
            
            return {
                "enhanced_prompt": enhanced_prompt,
                "context": context,
                "sources": sources,
                "has_knowledge": True,
                "knowledge_used": len(sources)
            }
            
        except Exception as e:
            logger.error(f"Error enhancing prompt with knowledge: {e}")
            return {
                "enhanced_prompt": user_message,
                "context": "",
                "sources": [],
                "has_knowledge": False,
                "error": str(e)
            }
    
    def _build_enhanced_prompt(self, user_message: str, context: str) -> str:
        """
        Build enhanced prompt with context
        
        Args:
            user_message: Original user message
            context: Relevant context from knowledge base
            
        Returns:
            Enhanced prompt string
        """
        if not context.strip():
            return user_message
        
        enhanced_prompt = f"""You have access to relevant information from your knowledge base. Use this information to provide a more accurate and helpful response.

RELEVANT KNOWLEDGE:
{context}

USER QUESTION: {user_message}

Please provide a helpful response based on the knowledge above and your general capabilities. If the knowledge is relevant, reference it in your response. If the knowledge doesn't fully answer the question, use your general knowledge to supplement."""
        
        return enhanced_prompt
    
    async def get_knowledge_summary(
        self,
        agent_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get a summary of the agent's knowledge base
        
        Args:
            agent_id: ID of the agent
            db: Database session
            
        Returns:
            Summary of knowledge base
        """
        try:
            service = get_knowledge_service(db)
            stats = service.get_knowledge_stats(agent_id)
            
            # Obtener documentos recientes
            recent_docs = service.get_agent_documents(
                agent_id=agent_id,
                skip=0,
                limit=5
            )
            
            return {
                "statistics": stats,
                "recent_documents": [
                    {
                        "id": doc.id,
                        "filename": doc.filename,
                        "status": doc.status,
                        "created_at": doc.created_at
                    }
                    for doc in recent_docs
                ],
                "has_knowledge": (stats.get("total_documents", 0) > 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting knowledge summary: {e}")
            return {
                "statistics": None,
                "recent_documents": [],
                "has_knowledge": False,
                "error": str(e)
            }
    
    async def suggest_questions(
        self,
        agent_id: int,
        db: Session,
        limit: int = 5
    ) -> List[str]:
        """
        Suggest questions based on the agent's knowledge base
        
        Args:
            agent_id: ID of the agent
            db: Database session
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested questions
        """
        try:
            service = get_knowledge_service(db)
            # Obtener algunos documentos para generar sugerencias
            documents = service.get_agent_documents(
                agent_id=agent_id,
                skip=0,
                limit=3
            )
            
            suggestions = []
            for doc in documents:
                # Generar sugerencias basadas en el nombre del archivo
                filename_base = doc.filename.split('.')[0].replace('_', ' ').replace('-', ' ')
                suggestions.extend([
                    f"¿Qué información tienes sobre {filename_base}?",
                    f"Explícame el contenido de {doc.filename}",
                    f"¿Puedes resumir {filename_base}?"
                ])
            
            # Agregar sugerencias generales
            if documents:
                suggestions.extend([
                    "¿Qué documentos tienes disponibles?",
                    "¿Puedes darme un resumen de tu conocimiento?",
                    "¿Sobre qué temas puedes ayudarme?"
                ])
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Error suggesting questions: {e}")
            return []
    
    def format_response_with_sources(
        self,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> str:
        """
        Format response with source citations
        
        Args:
            response: AI response
            sources: List of sources used
            
        Returns:
            Formatted response with citations
        """
        if not sources:
            return response
        
        # Agregar referencias al final
        citations = "\n\n📚 **Fuentes consultadas:**\n"
        for i, source in enumerate(sources, 1):
            citations += f"{i}. {source['filename']} (similitud: {source['similarity_score']:.2f})\n"
        
        return response + citations


# Global RAG service instance
rag_service = RAGService()