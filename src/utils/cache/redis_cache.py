"""
Redis-based caching system for StrawberryBot.

This module provides a high-performance caching layer using Redis,
with support for:
- Asynchronous operations
- Key prefixing
- TTL management
- JSON serialization
- Type hints
"""

import json
from typing import Any, Optional, Union, Dict, List
from datetime import timedelta
import redis.asyncio as redis
import orjson
from src.config.settings import get_config

class RedisCache:
    """
    Asynchronous Redis cache manager with type support and automatic serialization.
    
    Features:
    - Async/await support
    - Automatic JSON serialization/deserialization
    - Key prefixing for namespacing
    - Configurable TTL
    - Type hints for better IDE support
    """
    
    def __init__(self, prefix: str = "strawberry:", default_ttl: int = 3600):
        """
        Initialize the Redis cache manager.
        
        Args:
            prefix: Prefix for all keys to prevent collisions
            default_ttl: Default time-to-live in seconds
        """
        self.prefix = prefix
        self.default_ttl = default_ttl
        self._redis: Optional[redis.Redis] = None
        self._config = get_config("redis")
    
    async def connect(self) -> None:
        """
        Establish connection to Redis server.
        Should be called before any other operations.
        """
        if not self._redis:
            self._redis = redis.Redis(
                host=self._config['host'],
                port=self._config['port'],
                db=self._config["db"],
                password=self._config["password"],
                decode_responses=True
            )
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    def _make_key(self, key: str) -> str:
        """
        Create a prefixed key to prevent collisions.
        
        Args:
            key: Original key
            
        Returns:
            Prefixed key
        """
        return f"{self.prefix}{key}"
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            default: Default value if key doesn't exist
            
        Returns:
            Cached value or default
        """
        if not self._redis:
            await self.connect()
        
        value = await self._redis.get(self._make_key(key))
        if value is None:
            return default
        
        try:
            return orjson.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds or timedelta
            
        Returns:
            True if successful
        """
        if not self._redis:
            await self.connect()
        
        # Convert value to JSON if needed
        if not isinstance(value, (str, int, float, bool)):
            value = orjson.dumps(value).decode()
        
        # Handle TTL
        if isinstance(ttl, timedelta):
            ttl = int(ttl.total_seconds())
        elif ttl is None:
            ttl = self.default_ttl
        
        return await self._redis.set(
            self._make_key(key),
            value,
            ex=ttl
        )
    
    async def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted
        """
        if not self._redis:
            await self.connect()
        
        return bool(await self._redis.delete(self._make_key(key)))
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        if not self._redis:
            await self.connect()
        
        return bool(await self._redis.exists(self._make_key(key)))
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a numeric value.
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            New value
        """
        if not self._redis:
            await self.connect()
        
        return await self._redis.incrby(self._make_key(key), amount)
    
    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """
        Set expiration on key.
        
        Args:
            key: Cache key
            ttl: Time-to-live in seconds or timedelta
            
        Returns:
            True if successful
        """
        if not self._redis:
            await self.connect()
        
        if isinstance(ttl, timedelta):
            ttl = int(ttl.total_seconds())
        
        return await self._redis.expire(self._make_key(key), ttl)
    
    async def clear_prefix(self, prefix: str) -> int:
        """
        Clear all keys with a specific prefix.
        
        Args:
            prefix: Prefix to clear
            
        Returns:
            Number of keys cleared
        """
        if not self._redis:
            await self.connect()
        
        pattern = f"{self.prefix}{prefix}*"
        keys = await self._redis.keys(pattern)
        if keys:
            return await self._redis.delete(*keys)
        return 0
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values at once.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary of key-value pairs
        """
        if not self._redis:
            await self.connect()
        
        prefixed_keys = [self._make_key(key) for key in keys]
        values = await self._redis.mget(prefixed_keys)
        
        result = {}
        for key, value in zip(keys, values):
            if value is not None:
                try:
                    result[key] = orjson.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
        
        return result
    
    async def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """
        Set multiple key-value pairs at once.
        
        Args:
            mapping: Dictionary of key-value pairs to cache
            ttl: Time-to-live in seconds or timedelta
            
        Returns:
            True if successful
        """
        if not self._redis:
            await self.connect()
        
        # Convert values to JSON if needed
        prefixed_mapping = {}
        for key, value in mapping.items():
            if not isinstance(value, (str, int, float, bool)):
                value = orjson.dumps(value).decode()
            prefixed_mapping[self._make_key(key)] = value
        
        # Handle TTL
        if isinstance(ttl, timedelta):
            ttl = int(ttl.total_seconds())
        elif ttl is None:
            ttl = self.default_ttl
        
        # Use pipeline for atomic operation
        async with self._redis.pipeline() as pipe:
            await pipe.mset(prefixed_mapping)
            for key in prefixed_mapping:
                await pipe.expire(key, ttl)
            await pipe.execute()
        
        return True 