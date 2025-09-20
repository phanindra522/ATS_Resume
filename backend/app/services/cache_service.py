"""
Advanced Caching Service for ATS System
Supports Redis, in-memory caching with multiple strategies for token optimization
"""
import hashlib
import json
import pickle
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union, List
from cachetools import TTLCache, LFUCache
import logging

# Setup logger
logger = logging.getLogger(__name__)

class CacheBackend(ABC):
    """Abstract base class for cache backends"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries"""
        pass

class RedisCache(CacheBackend):
    """Redis-based cache backend for distributed caching"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", prefix: str = "ats"):
        self.redis_url = redis_url
        self.prefix = prefix
        self._redis = None
    
    async def _get_redis(self):
        """Lazy Redis connection"""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                await self._redis.ping()
                logger.info("Redis cache backend initialized")
            except ImportError:
                logger.error("Redis not available. Install with: pip install redis")
                raise ImportError("Redis package not installed")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                raise
        return self._redis
    
    def _make_key(self, key: str) -> str:
        """Create prefixed cache key"""
        return f"{self.prefix}:{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            redis = await self._get_redis()
            data = await redis.get(self._make_key(key))
            if data:
                return pickle.loads(data.encode('latin-1'))
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        try:
            redis = await self._get_redis()
            data = pickle.dumps(value).decode('latin-1')
            await redis.setex(self._make_key(key), ttl, data)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            redis = await self._get_redis()
            result = await redis.delete(self._make_key(key))
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        try:
            redis = await self._get_redis()
            result = await redis.exists(self._make_key(key))
            return result > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    async def clear(self) -> bool:
        try:
            redis = await self._get_redis()
            keys = await redis.keys(f"{self.prefix}:*")
            if keys:
                await redis.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False

class MemoryCache(CacheBackend):
    """In-memory cache backend with LFU eviction"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache = TTLCache(maxsize=max_size, ttl=ttl)
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            return self.cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        async with self._lock:
            self.cache[key] = value
            return True
    
    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        async with self._lock:
            return key in self.cache
    
    async def clear(self) -> bool:
        async with self._lock:
            self.cache.clear()
            return True

class CacheService:
    """Unified cache service with multiple backends and strategies"""
    
    def __init__(self, 
                 primary_backend: CacheBackend,
                 fallback_backend: Optional[CacheBackend] = None):
        self.primary = primary_backend
        self.fallback = fallback_backend or MemoryCache(max_size=500, ttl=1800)
        
    def _generate_cache_key(self, namespace: str, identifier: str, **kwargs) -> str:
        """Generate deterministic cache key from content"""
        # Create hash from identifier and kwargs for consistency
        content = f"{identifier}:{json.dumps(kwargs, sort_keys=True)}"
        hash_obj = hashlib.sha256(content.encode())
        return f"{namespace}:{hash_obj.hexdigest()[:16]}"
    
    async def get(self, namespace: str, identifier: str, **kwargs) -> Optional[Any]:
        """Get from cache with fallback"""
        key = self._generate_cache_key(namespace, identifier, **kwargs)
        
        # Try primary cache first
        result = await self.primary.get(key)
        if result is not None:
            logger.debug(f"Cache HIT (primary): {key}")
            return result
        
        # Try fallback cache
        result = await self.fallback.get(key)
        if result is not None:
            logger.debug(f"Cache HIT (fallback): {key}")
            # Warm primary cache
            await self.primary.set(key, result)
            return result
        
        logger.debug(f"Cache MISS: {key}")
        return None
    
    async def set(self, namespace: str, identifier: str, value: Any, 
                  ttl: int = 3600, **kwargs) -> bool:
        """Set in both caches"""
        key = self._generate_cache_key(namespace, identifier, **kwargs)
        
        # Set in both caches
        primary_success = await self.primary.set(key, value, ttl)
        fallback_success = await self.fallback.set(key, value, ttl)
        
        logger.debug(f"Cache SET: {key} (primary: {primary_success}, fallback: {fallback_success})")
        return primary_success or fallback_success
    
    async def delete(self, namespace: str, identifier: str, **kwargs) -> bool:
        """Delete from both caches"""
        key = self._generate_cache_key(namespace, identifier, **kwargs)
        
        primary_result = await self.primary.delete(key)
        fallback_result = await self.fallback.delete(key)
        
        return primary_result or fallback_result
    
    async def clear_namespace(self, namespace: str) -> bool:
        """Clear all entries for a namespace (basic implementation)"""
        # Note: This is a simple implementation. For production, 
        # you'd want Redis SCAN with pattern matching
        await self.primary.clear()
        await self.fallback.clear()
        return True

# Cache decorators for easy usage
def cached(namespace: str, ttl: int = 3600, cache_service: Optional[CacheService] = None):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Use global cache service if none provided
            service = cache_service or get_cache_service()
            
            # Generate cache identifier from function name and args
            func_name = f"{func.__module__}.{func.__name__}"
            args_str = f"{args}:{kwargs}"
            
            # Try to get from cache
            result = await service.get(namespace, func_name, args=args_str)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await service.set(namespace, func_name, result, ttl, args=args_str)
            
            return result
        return wrapper
    return decorator

# Global cache service instance
_cache_service = None

def get_cache_service() -> CacheService:
    """Get global cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = create_cache_service()
    return _cache_service

def create_cache_service(use_redis: bool = True) -> CacheService:
    """Factory function to create cache service"""
    try:
        if use_redis:
            primary = RedisCache()
            fallback = MemoryCache(max_size=1000, ttl=3600)
            logger.info("Cache service created with Redis primary + Memory fallback")
        else:
            primary = MemoryCache(max_size=2000, ttl=3600)
            fallback = None
            logger.info("Cache service created with Memory only")
        
        return CacheService(primary, fallback)
    except Exception as e:
        logger.warning(f"Failed to create Redis cache, using memory only: {e}")
        primary = MemoryCache(max_size=2000, ttl=3600)
        return CacheService(primary, None)

# Cache statistics and monitoring
class CacheStats:
    """Cache statistics tracking"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.errors = 0
        
    def hit(self):
        self.hits += 1
    
    def miss(self):
        self.misses += 1
    
    def set_operation(self):
        self.sets += 1
    
    def error(self):
        self.errors += 1
    
    @property
    def hit_ratio(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "errors": self.errors,
            "hit_ratio": self.hit_ratio,
            "total_operations": self.hits + self.misses
        }

# Global stats instance
cache_stats = CacheStats()