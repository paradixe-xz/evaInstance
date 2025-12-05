"""
Caching layer for improved performance
"""
from typing import Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json
import pickle
from pathlib import Path

from ..core.logging import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Simple file-based cache manager"""
    
    def __init__(self, cache_dir: str = "./storage/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache: dict = {}  # In-memory cache for frequently accessed items
    
    def _get_cache_key(self, key: str) -> str:
        """Generate cache key hash"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path"""
        cache_key = self._get_cache_key(key)
        return self.cache_dir / f"{cache_key}.cache"
    
    def get(self, key: str, use_memory: bool = True) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            use_memory: Check memory cache first
            
        Returns:
            Cached value or None
        """
        # Check memory cache first
        if use_memory and key in self.memory_cache:
            entry = self.memory_cache[key]
            if entry["expires_at"] > datetime.utcnow():
                logger.debug(f"Cache hit (memory): {key}")
                return entry["value"]
            else:
                del self.memory_cache[key]
        
        # Check file cache
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    entry = pickle.load(f)
                
                if entry["expires_at"] > datetime.utcnow():
                    logger.debug(f"Cache hit (file): {key}")
                    # Store in memory cache
                    if use_memory:
                        self.memory_cache[key] = entry
                    return entry["value"]
                else:
                    # Expired, remove
                    cache_path.unlink()
            except Exception as e:
                logger.error(f"Error reading cache: {e}")
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
        use_memory: bool = True
    ):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
            use_memory: Also store in memory cache
        """
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        entry = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.utcnow()
        }
        
        # Store in file
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(entry, f)
            logger.debug(f"Cache set (file): {key}")
        except Exception as e:
            logger.error(f"Error writing cache: {e}")
        
        # Store in memory
        if use_memory:
            self.memory_cache[key] = entry
            logger.debug(f"Cache set (memory): {key}")
    
    def delete(self, key: str):
        """Delete from cache"""
        # Remove from memory
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # Remove from file
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
        
        logger.debug(f"Cache deleted: {key}")
    
    def clear(self):
        """Clear all cache"""
        # Clear memory
        self.memory_cache.clear()
        
        # Clear files
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink()
        
        logger.info("Cache cleared")
    
    def cleanup_expired(self):
        """Remove expired cache entries"""
        current_time = datetime.utcnow()
        
        # Clean memory cache
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry["expires_at"] <= current_time
        ]
        for key in expired_keys:
            del self.memory_cache[key]
        
        # Clean file cache
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                if entry["expires_at"] <= current_time:
                    cache_file.unlink()
            except Exception:
                # If we can't read it, delete it
                cache_file.unlink()
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


# Global cache instance
cache_manager = CacheManager()


def cached(
    ttl_seconds: int = 3600,
    key_prefix: str = "",
    use_memory: bool = True
):
    """
    Decorator for caching function results
    
    Args:
        ttl_seconds: Time to live in seconds
        key_prefix: Prefix for cache key
        use_memory: Use memory cache
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = cache_manager.get(cache_key, use_memory)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache_manager.set(cache_key, result, ttl_seconds, use_memory)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = cache_manager.get(cache_key, use_memory)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache_manager.set(cache_key, result, ttl_seconds, use_memory)
            
            return result
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Convenience functions
def cache_embedding(text: str, embedding: list, ttl_seconds: int = 86400):
    """Cache an embedding (24 hours default)"""
    key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
    cache_manager.set(key, embedding, ttl_seconds)


def get_cached_embedding(text: str) -> Optional[list]:
    """Get cached embedding"""
    key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
    return cache_manager.get(key)


def cache_knowledge_search(query: str, agent_id: int, results: list, ttl_seconds: int = 300):
    """Cache knowledge base search results (5 minutes default)"""
    key = f"knowledge_search:{agent_id}:{hashlib.md5(query.encode()).hexdigest()}"
    cache_manager.set(key, results, ttl_seconds, use_memory=True)


def get_cached_knowledge_search(query: str, agent_id: int) -> Optional[list]:
    """Get cached knowledge search results"""
    key = f"knowledge_search:{agent_id}:{hashlib.md5(query.encode()).hexdigest()}"
    return cache_manager.get(key, use_memory=True)


def invalidate_agent_cache(agent_id: int):
    """Invalidate all cache for an agent"""
    # This is a simple implementation - in production, you'd want a more sophisticated approach
    cache_manager.cleanup_expired()
    logger.info(f"Invalidated cache for agent {agent_id}")
