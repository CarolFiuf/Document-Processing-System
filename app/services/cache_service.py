import redis
import json
import logging
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Cache service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def get_document_status(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get cached document status"""
        if not self.redis_client:
            return None
        
        try:
            cached = self.redis_client.get(f"status:{doc_id}")
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get error for status:{doc_id}: {e}")
        
        return None
    
    async def set_document_status(self, doc_id: str, status_data: Dict[str, Any], expire_seconds: int = 30):
        """Cache document status"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.setex(
                f"status:{doc_id}",
                expire_seconds,
                json.dumps(status_data, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache set error for status:{doc_id}: {e}")
    
    async def get_document_results(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get cached document results"""
        if not self.redis_client:
            return None
        
        try:
            cached = self.redis_client.get(f"results:{doc_id}")
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get error for results:{doc_id}: {e}")
        
        return None
    
    async def set_document_results(self, doc_id: str, results_data: Dict[str, Any], expire_seconds: int = 3600):
        """Cache document results"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.setex(
                f"results:{doc_id}",
                expire_seconds,
                json.dumps(results_data, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache set error for results:{doc_id}: {e}")
    
    async def clear_document_cache(self, doc_id: str):
        """Clear all cached data for a document"""
        if not self.redis_client:
            return
        
        try:
            keys_to_delete = [
                f"status:{doc_id}",
                f"results:{doc_id}",
                f"insights:{doc_id}"
            ]
            
            for key in keys_to_delete:
                self.redis_client.delete(key)
                
        except Exception as e:
            logger.warning(f"Cache clear error for doc {doc_id}: {e}")
    
    async def get_processing_stats(self) -> Optional[Dict[str, Any]]:
        """Get cached processing statistics"""
        if not self.redis_client:
            return None
        
        try:
            cached = self.redis_client.get("processing_stats")
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get error for processing_stats: {e}")
        
        return None
    
    async def set_processing_stats(self, stats_data: Dict[str, Any], expire_seconds: int = 300):
        """Cache processing statistics"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.setex(
                "processing_stats",
                expire_seconds,
                json.dumps(stats_data, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache set error for processing_stats: {e}")