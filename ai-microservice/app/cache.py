"""
Redis-based caching system for ML predictions.

This module provides a high-performance caching layer using Redis to reduce
redundant model predictions and improve response times.
"""

import json
import hashlib
from typing import Optional, Any, Dict
from datetime import timedelta
import redis.asyncio as redis
from loguru import logger

from app.config import settings


class CacheManager:
    """Async Redis cache manager for prediction results."""
    
    def __init__(self):
        """Initialize cache manager with Redis connection pool."""
        self.enabled = settings.REDIS_ENABLED
        self.redis_client: Optional[redis.Redis] = None
        self._connection_pool: Optional[redis.ConnectionPool] = None
        
    async def connect(self):
        """Establish connection to Redis server."""
        if not self.enabled:
            logger.info("Redis caching is disabled")
            return
            
        try:
            self._connection_pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=50,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            
            self.redis_client = redis.Redis(connection_pool=self._connection_pool)
            
            # Test connection
            await self.redis_client.ping()
            logger.info(f"✅ Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Caching disabled.")
            self.enabled = False
            self.redis_client = None
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            if self._connection_pool:
                await self._connection_pool.disconnect()
            logger.info("Redis connection closed")
    
    def _generate_cache_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """
        Generate deterministic cache key from request data.
        
        Args:
            prefix: Key prefix (e.g., 'flood_risk', 'nowcast')
            data: Request parameters dictionary
            
        Returns:
            Hashed cache key
        """
        # Sort dictionary to ensure consistent ordering
        sorted_data = json.dumps(data, sort_keys=True, default=str)
        
        # Generate SHA256 hash
        hash_object = hashlib.sha256(sorted_data.encode())
        hash_hex = hash_object.hexdigest()[:16]  # Use first 16 chars
        
        return f"{prefix}:{hash_hex}"
    
    async def get(self, prefix: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached prediction result.
        
        Args:
            prefix: Cache key prefix
            data: Request parameters
            
        Returns:
            Cached result or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(prefix, data)
            cached_value = await self.redis_client.get(cache_key)
            
            if cached_value:
                logger.debug(f"✅ Cache hit: {cache_key}")
                return json.loads(cached_value)
            else:
                logger.debug(f"❌ Cache miss: {cache_key}")
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        prefix: str,
        data: Dict[str, Any],
        result: Dict[str, Any],
        ttl: int
    ) -> bool:
        """
        Store prediction result in cache.
        
        Args:
            prefix: Cache key prefix
            data: Request parameters
            result: Prediction result to cache
            ttl: Time-to-live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(prefix, data)
            serialized_result = json.dumps(result, default=str)
            
            await self.redis_client.setex(
                cache_key,
                timedelta(seconds=ttl),
                serialized_result
            )
            
            logger.debug(f"✅ Cached: {cache_key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, prefix: str, data: Dict[str, Any]) -> bool:
        """
        Delete cached result.
        
        Args:
            prefix: Cache key prefix
            data: Request parameters
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(prefix, data)
            deleted = await self.redis_client.delete(cache_key)
            logger.debug(f"🗑️ Deleted cache: {cache_key}")
            return deleted > 0
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def clear_prefix(self, prefix: str) -> int:
        """
        Clear all cache entries with given prefix.
        
        Args:
            prefix: Cache key prefix to clear
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            pattern = f"{prefix}:*"
            keys = []
            
            # Scan for keys matching pattern (safer than KEYS for production)
            async for key in self.redis_client.scan_iter(match=pattern, count=100):
                keys.append(key)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"🗑️ Cleared {deleted} cache entries with prefix '{prefix}'")
                return deleted
            else:
                logger.debug(f"No cache entries found with prefix '{prefix}'")
                return 0
                
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    async def clear_all(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            await self.redis_client.flushdb()
            logger.info("🗑️ Cleared all cache entries")
            return True
            
        except Exception as e:
            logger.error(f"Cache clear all error: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled or not self.redis_client:
            return {
                "enabled": False,
                "status": "disabled"
            }
        
        try:
            info = await self.redis_client.info("stats")
            memory_info = await self.redis_client.info("memory")
            
            return {
                "enabled": True,
                "status": "connected",
                "total_keys": await self.redis_client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
                ),
                "memory_used_mb": memory_info.get("used_memory", 0) / (1024 * 1024),
                "memory_peak_mb": memory_info.get("used_memory_peak", 0) / (1024 * 1024),
            }
            
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {
                "enabled": True,
                "status": "error",
                "error": str(e)
            }


# Global cache manager instance
cache_manager = CacheManager()
