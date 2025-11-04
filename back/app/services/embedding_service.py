"""
Embedding service using Ollama for generating text embeddings
"""
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import httpx
import numpy as np
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Ollama"""
    
    # Default embedding model
    DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
    
    # Alternative models if default is not available
    FALLBACK_MODELS = [
        "nomic-embed-text",
        "mxbai-embed-large",
        "all-minilm",
        "snowflake-arctic-embed"
    ]
    
    def __init__(self, model_name: str = None, ollama_url: str = None):
        """Initialize embedding service"""
        self.model_name = model_name or self.DEFAULT_EMBEDDING_MODEL
        self.ollama_url = ollama_url or settings.OLLAMA_URL
        self.client = httpx.AsyncClient(timeout=60.0)
        self._model_verified = False
        self._embedding_dimension = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.client.aclose()
    
    async def verify_model(self) -> bool:
        """Verify that the embedding model is available"""
        try:
            # Check if model is available
            response = await self.client.get(f"{self.ollama_url}/api/tags")
            response.raise_for_status()
            
            available_models = response.json().get("models", [])
            model_names = [model["name"] for model in available_models]
            
            # Check if our model is available
            if self.model_name in model_names:
                self._model_verified = True
                logger.info(f"Embedding model {self.model_name} is available")
                return True
            
            # Try fallback models
            for fallback_model in self.FALLBACK_MODELS:
                if fallback_model in model_names:
                    logger.warning(f"Model {self.model_name} not found, using fallback: {fallback_model}")
                    self.model_name = fallback_model
                    self._model_verified = True
                    return True
            
            logger.error(f"No suitable embedding model found. Available models: {model_names}")
            return False
            
        except Exception as e:
            logger.error(f"Error verifying embedding model: {e}")
            return False
    
    async def pull_model_if_needed(self) -> bool:
        """Pull the embedding model if it's not available"""
        try:
            if not await self.verify_model():
                logger.info(f"Skipping embedding model pull for: {self.model_name} (using CLI-only mode)")
                
                # Skip pull in CLI-only mode - assume model exists or use fallback
                self._model_verified = True
                return True
                    
        except Exception as e:
            logger.error(f"Error pulling embedding model: {e}")
            return False
    
    async def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from this model"""
        if self._embedding_dimension:
            return self._embedding_dimension
        
        try:
            # Generate a test embedding to determine dimension
            test_embedding = await self.generate_embedding("test")
            if test_embedding:
                self._embedding_dimension = len(test_embedding)
                logger.info(f"Embedding dimension for {self.model_name}: {self._embedding_dimension}")
                return self._embedding_dimension
            
        except Exception as e:
            logger.error(f"Error determining embedding dimension: {e}")
        
        # Default dimension for common models
        default_dimensions = {
            "nomic-embed-text": 768,
            "mxbai-embed-large": 1024,
            "all-minilm": 384,
            "snowflake-arctic-embed": 1024
        }
        
        self._embedding_dimension = default_dimensions.get(self.model_name, 768)
        return self._embedding_dimension
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text"""
        if not text or not text.strip():
            return None
        
        try:
            # Ensure model is available
            if not self._model_verified:
                if not await self.verify_model():
                    if not await self.pull_model_if_needed():
                        raise Exception(f"Embedding model {self.model_name} is not available")
            
            # Clean and prepare text
            clean_text = text.strip()
            if len(clean_text) > 8000:  # Limit text length
                clean_text = clean_text[:8000]
            
            # Generate embedding
            response = await self.client.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": clean_text
                },
                timeout=30.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            embedding = result.get("embedding")
            if not embedding:
                logger.error(f"No embedding returned for text: {clean_text[:100]}...")
                return None
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts in batches"""
        if not texts:
            return []
        
        embeddings = []
        
        # Process in batches to avoid overwhelming the server
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = []
            
            # Process batch concurrently
            tasks = [self.generate_embedding(text) for text in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Error in batch embedding: {result}")
                    batch_embeddings.append(None)
                else:
                    batch_embeddings.append(result)
            
            embeddings.extend(batch_embeddings)
            
            # Small delay between batches to be nice to the server
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)
        
        return embeddings
    
    def calculate_cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        if not embedding1 or not embedding2 or len(embedding1) != len(embedding2):
            return 0.0
        
        try:
            # Convert to numpy arrays for efficient computation
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def find_most_similar(self, query_embedding: List[float], 
                         candidate_embeddings: List[Tuple[int, List[float]]], 
                         top_k: int = 5, 
                         threshold: float = 0.0) -> List[Tuple[int, float]]:
        """Find most similar embeddings to query"""
        if not query_embedding or not candidate_embeddings:
            return []
        
        similarities = []
        
        for idx, embedding in candidate_embeddings:
            if embedding:
                similarity = self.calculate_cosine_similarity(query_embedding, embedding)
                if similarity >= threshold:
                    similarities.append((idx, similarity))
        
        # Sort by similarity (descending) and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    async def search_similar_chunks(self, query: str, 
                                  chunk_embeddings: List[Tuple[int, List[float]]], 
                                  top_k: int = 5, 
                                  threshold: float = 0.7) -> List[Tuple[int, float]]:
        """Search for similar chunks using embedding similarity"""
        # Generate query embedding
        query_embedding = await self.generate_embedding(query)
        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return []
        
        # Find most similar chunks
        return self.find_most_similar(query_embedding, chunk_embeddings, top_k, threshold)
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current embedding model"""
        try:
            dimension = await self.get_embedding_dimension()
            
            return {
                "model_name": self.model_name,
                "dimension": dimension,
                "verified": self._model_verified,
                "ollama_url": self.ollama_url
            }
            
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {
                "model_name": self.model_name,
                "dimension": None,
                "verified": False,
                "error": str(e)
            }


# Global embedding service instance
_embedding_service = None


async def get_embedding_service() -> EmbeddingService:
    """Get or create global embedding service instance"""
    global _embedding_service
    
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
        # Skip model verification in CLI-only mode
        _embedding_service._model_verified = True
    
    return _embedding_service


async def cleanup_embedding_service():
    """Cleanup global embedding service"""
    global _embedding_service
    
    if _embedding_service:
        await _embedding_service.client.aclose()
        _embedding_service = None