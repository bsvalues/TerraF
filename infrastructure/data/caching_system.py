"""
Cross-Service Caching System for TerraFlow Platform

This module implements a multi-level caching system with intelligent invalidation
to improve performance across services in the TerraFlow platform.
"""

import os
import json
import time
import hashlib
import logging
import threading
import pickle
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Set, Tuple, Union, TypeVar, Generic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variable for cache values
T = TypeVar('T')

class CacheLevel(Enum):
    """Cache levels in the system"""
    L1 = "l1"  # Fast, in-memory cache
    L2 = "l2"  # Distributed cache (Redis)
    L3 = "l3"  # Persistent cache (disk)

class CacheStrategy(Enum):
    """Cache invalidation strategies"""
    TTL = "ttl"  # Time-to-live based invalidation
    LRU = "lru"  # Least recently used invalidation
    FIFO = "fifo"  # First in, first out invalidation
    TAGS = "tags"  # Tag-based invalidation

class CacheEntry(Generic[T]):
    """
    An entry in the cache
    
    This class represents a single cached value with metadata.
    """
    
    def __init__(self,
                key: str,
                value: T,
                expiry: Optional[float] = None,
                tags: Optional[List[str]] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a new cache entry
        
        Args:
            key: Cache key
            value: Cached value
            expiry: Optional expiration timestamp
            tags: Optional tags for tag-based invalidation
            metadata: Optional metadata
        """
        self.key = key
        self.value = value
        self.expiry = expiry
        self.tags = tags or []
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.accessed_at = time.time()
        self.access_count = 0
    
    def is_expired(self) -> bool:
        """Check if this entry is expired"""
        if self.expiry is None:
            return False
        
        return time.time() > self.expiry
    
    def access(self):
        """Mark this entry as accessed"""
        self.accessed_at = time.time()
        self.access_count += 1
    
    def has_tag(self, tag: str) -> bool:
        """Check if this entry has a specific tag"""
        return tag in self.tags

class MemoryCache(Generic[T]):
    """
    In-memory cache implementation (L1)
    
    This class provides a fast, in-memory cache for frequently accessed data.
    """
    
    def __init__(self, max_size: int = 1000, strategy: CacheStrategy = CacheStrategy.LRU):
        """
        Initialize a new memory cache
        
        Args:
            max_size: Maximum number of entries to store
            strategy: Cache invalidation strategy
        """
        self.max_size = max_size
        self.strategy = strategy
        self.cache = {}  # key -> CacheEntry
        self.tag_index = {}  # tag -> Set[key]
        self.access_order = []  # List of keys in access order (for LRU)
        self.insertion_order = []  # List of keys in insertion order (for FIFO)
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[T]:
        """
        Get a value from the cache
        
        Args:
            key: Cache key
            
        Returns:
            Optional[T]: The cached value, or None if not found or expired
        """
        with self.lock:
            entry = self.cache.get(key)
            
            if entry is None:
                return None
            
            # Check if expired
            if entry.is_expired():
                self._remove_entry(key)
                return None
            
            # Update access time and count
            entry.access()
            
            # Update access order for LRU
            if self.strategy == CacheStrategy.LRU:
                if key in self.access_order:
                    self.access_order.remove(key)
                self.access_order.append(key)
            
            return entry.value
    
    def set(self, key: str, value: T, ttl: Optional[float] = None, tags: Optional[List[str]] = None) -> bool:
        """
        Set a value in the cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time-to-live in seconds
            tags: Optional tags for tag-based invalidation
            
        Returns:
            bool: True if the value was cached, False otherwise
        """
        with self.lock:
            # Create expiry timestamp if TTL is provided
            expiry = time.time() + ttl if ttl is not None else None
            
            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                expiry=expiry,
                tags=tags
            )
            
            # If key already exists, update it
            if key in self.cache:
                old_entry = self.cache[key]
                
                # Remove old entry from tag index
                for tag in old_entry.tags:
                    if tag in self.tag_index and key in self.tag_index[tag]:
                        self.tag_index[tag].remove(key)
                
                # Update entry
                self.cache[key] = entry
                
                # Update access order for LRU
                if self.strategy == CacheStrategy.LRU and key in self.access_order:
                    self.access_order.remove(key)
                    self.access_order.append(key)
                
                # Update insertion order for FIFO
                if self.strategy == CacheStrategy.FIFO and key in self.insertion_order:
                    self.insertion_order.remove(key)
                    self.insertion_order.append(key)
                
            else:
                # Check if cache is full
                if len(self.cache) >= self.max_size:
                    self._evict_entries()
                
                # Add new entry
                self.cache[key] = entry
                
                # Update access order for LRU
                if self.strategy == CacheStrategy.LRU:
                    self.access_order.append(key)
                
                # Update insertion order for FIFO
                if self.strategy == CacheStrategy.FIFO:
                    self.insertion_order.append(key)
            
            # Update tag index
            for tag in tags or []:
                if tag not in self.tag_index:
                    self.tag_index[tag] = set()
                self.tag_index[tag].add(key)
            
            return True
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if the value was deleted, False otherwise
        """
        with self.lock:
            return self._remove_entry(key)
    
    def clear(self):
        """Clear the cache"""
        with self.lock:
            self.cache = {}
            self.tag_index = {}
            self.access_order = []
            self.insertion_order = []
    
    def invalidate_by_tag(self, tag: str) -> int:
        """
        Invalidate all entries with a specific tag
        
        Args:
            tag: Tag to invalidate
            
        Returns:
            int: Number of entries invalidated
        """
        with self.lock:
            if tag not in self.tag_index:
                return 0
            
            keys = list(self.tag_index[tag])
            count = 0
            
            for key in keys:
                if self._remove_entry(key):
                    count += 1
            
            return count
    
    def invalidate_by_prefix(self, prefix: str) -> int:
        """
        Invalidate all entries with keys starting with a specific prefix
        
        Args:
            prefix: Key prefix to invalidate
            
        Returns:
            int: Number of entries invalidated
        """
        with self.lock:
            keys = [key for key in self.cache.keys() if key.startswith(prefix)]
            count = 0
            
            for key in keys:
                if self._remove_entry(key):
                    count += 1
            
            return count
    
    def _remove_entry(self, key: str) -> bool:
        """
        Remove an entry from the cache
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if the entry was removed, False otherwise
        """
        if key not in self.cache:
            return False
        
        entry = self.cache[key]
        
        # Remove from tag index
        for tag in entry.tags:
            if tag in self.tag_index and key in self.tag_index[tag]:
                self.tag_index[tag].remove(key)
                
                # Clean up empty tag sets
                if not self.tag_index[tag]:
                    del self.tag_index[tag]
        
        # Remove from access order
        if key in self.access_order:
            self.access_order.remove(key)
        
        # Remove from insertion order
        if key in self.insertion_order:
            self.insertion_order.remove(key)
        
        # Remove from cache
        del self.cache[key]
        
        return True
    
    def _evict_entries(self, count: int = 1):
        """
        Evict entries from the cache
        
        Args:
            count: Number of entries to evict
        """
        # First, evict expired entries
        expired_keys = [key for key, entry in self.cache.items() if entry.is_expired()]
        
        for key in expired_keys:
            self._remove_entry(key)
        
        # If we've evicted enough entries, return
        if len(expired_keys) >= count or len(self.cache) < self.max_size:
            return
        
        # Otherwise, evict based on strategy
        remaining = count - len(expired_keys)
        
        if self.strategy == CacheStrategy.LRU:
            # Evict least recently used entries
            for i in range(min(remaining, len(self.access_order))):
                if self.access_order:
                    key = self.access_order[0]  # Oldest access
                    self._remove_entry(key)
                    
        elif self.strategy == CacheStrategy.FIFO:
            # Evict oldest entries
            for i in range(min(remaining, len(self.insertion_order))):
                if self.insertion_order:
                    key = self.insertion_order[0]  # Oldest insertion
                    self._remove_entry(key)
    
    def size(self) -> int:
        """Get the number of entries in the cache"""
        return len(self.cache)

class RedisCache(Generic[T]):
    """
    Redis-based distributed cache implementation (L2)
    
    This class provides a distributed cache using Redis for sharing
    cache data across services.
    """
    
    def __init__(self, redis_client, prefix: str = "terraflow:cache:", ttl: int = 3600):
        """
        Initialize a new Redis cache
        
        Args:
            redis_client: Redis client instance
            prefix: Key prefix for Redis keys
            ttl: Default TTL in seconds
        """
        self.redis = redis_client
        self.prefix = prefix
        self.default_ttl = ttl
    
    def get(self, key: str) -> Optional[T]:
        """
        Get a value from the cache
        
        Args:
            key: Cache key
            
        Returns:
            Optional[T]: The cached value, or None if not found
        """
        redis_key = f"{self.prefix}{key}"
        
        try:
            # Get value from Redis
            data = self.redis.get(redis_key)
            
            if data is None:
                return None
            
            # Deserialize value
            entry = pickle.loads(data)
            
            # Update access time
            pipe = self.redis.pipeline()
            pipe.hincrby(f"{redis_key}:meta", "access_count", 1)
            pipe.hset(f"{redis_key}:meta", "accessed_at", time.time())
            pipe.execute()
            
            return entry
            
        except Exception as e:
            logger.error(f"Error getting value from Redis cache: {str(e)}")
            return None
    
    def set(self, key: str, value: T, ttl: Optional[int] = None, tags: Optional[List[str]] = None) -> bool:
        """
        Set a value in the cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL in seconds (defaults to instance TTL)
            tags: Optional tags for tag-based invalidation
            
        Returns:
            bool: True if the value was cached, False otherwise
        """
        redis_key = f"{self.prefix}{key}"
        
        try:
            # Serialize value
            data = pickle.dumps(value)
            
            # Set value in Redis
            pipe = self.redis.pipeline()
            
            # Set value with TTL
            expiry = ttl if ttl is not None else self.default_ttl
            pipe.setex(redis_key, expiry, data)
            
            # Set metadata
            pipe.hset(f"{redis_key}:meta", mapping={
                "created_at": time.time(),
                "accessed_at": time.time(),
                "access_count": 0
            })
            
            # Set tags
            if tags:
                # Add tags to key metadata
                pipe.sadd(f"{redis_key}:tags", *tags)
                
                # Add key to tag indexes
                for tag in tags:
                    pipe.sadd(f"{self.prefix}tag:{tag}", key)
            
            pipe.execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting value in Redis cache: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if the value was deleted, False otherwise
        """
        redis_key = f"{self.prefix}{key}"
        
        try:
            # Get tags for this key
            tags = self.redis.smembers(f"{redis_key}:tags")
            
            pipe = self.redis.pipeline()
            
            # Delete key and metadata
            pipe.delete(redis_key)
            pipe.delete(f"{redis_key}:meta")
            pipe.delete(f"{redis_key}:tags")
            
            # Remove key from tag indexes
            for tag in tags:
                pipe.srem(f"{self.prefix}tag:{tag}", key)
            
            pipe.execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting value from Redis cache: {str(e)}")
            return False
    
    def clear(self):
        """Clear the cache"""
        try:
            # Get all keys with prefix
            keys = self.redis.keys(f"{self.prefix}*")
            
            if keys:
                # Delete all keys
                self.redis.delete(*keys)
                
            return True
            
        except Exception as e:
            logger.error(f"Error clearing Redis cache: {str(e)}")
            return False
    
    def invalidate_by_tag(self, tag: str) -> int:
        """
        Invalidate all entries with a specific tag
        
        Args:
            tag: Tag to invalidate
            
        Returns:
            int: Number of entries invalidated
        """
        try:
            # Get all keys with this tag
            keys = self.redis.smembers(f"{self.prefix}tag:{tag}")
            
            if not keys:
                return 0
            
            count = 0
            
            # Delete each key
            for key in keys:
                if self.delete(key.decode('utf-8') if isinstance(key, bytes) else key):
                    count += 1
            
            # Delete tag index
            self.redis.delete(f"{self.prefix}tag:{tag}")
            
            return count
            
        except Exception as e:
            logger.error(f"Error invalidating by tag in Redis cache: {str(e)}")
            return 0
    
    def invalidate_by_prefix(self, prefix: str) -> int:
        """
        Invalidate all entries with keys starting with a specific prefix
        
        Args:
            prefix: Key prefix to invalidate
            
        Returns:
            int: Number of entries invalidated
        """
        try:
            # Get all keys with this prefix
            full_prefix = f"{self.prefix}{prefix}"
            keys = self.redis.keys(f"{full_prefix}*")
            
            # Filter out metadata and tag keys
            data_keys = [key for key in keys if not (key.endswith(b":meta") or key.endswith(b":tags"))]
            
            if not data_keys:
                return 0
            
            count = len(data_keys)
            
            # Delete all keys and metadata
            all_keys = set()
            for key in data_keys:
                all_keys.add(key)
                all_keys.add(f"{key}:meta")
                all_keys.add(f"{key}:tags")
            
            if all_keys:
                self.redis.delete(*all_keys)
            
            return count
            
        except Exception as e:
            logger.error(f"Error invalidating by prefix in Redis cache: {str(e)}")
            return 0

class DiskCache(Generic[T]):
    """
    Disk-based persistent cache implementation (L3)
    
    This class provides a persistent cache using disk storage for
    data that should be persisted across service restarts.
    """
    
    def __init__(self, cache_dir: str = "data/cache", ttl: int = 86400):
        """
        Initialize a new disk cache
        
        Args:
            cache_dir: Directory for cache files
            ttl: Default TTL in seconds (1 day)
        """
        self.cache_dir = cache_dir
        self.default_ttl = ttl
        self.metadata_dir = os.path.join(cache_dir, "metadata")
        self.data_dir = os.path.join(cache_dir, "data")
        self.tag_dir = os.path.join(cache_dir, "tags")
        
        # Create cache directories
        os.makedirs(self.metadata_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.tag_dir, exist_ok=True)
        
        # Start cleanup thread
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()
    
    def stop(self):
        """Stop the cleanup thread"""
        self.running = False
        if self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=1.0)
    
    def _get_hash(self, key: str) -> str:
        """Get a hash of a key for file names"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_data_path(self, key: str) -> str:
        """Get the path for data file"""
        key_hash = self._get_hash(key)
        return os.path.join(self.data_dir, key_hash)
    
    def _get_metadata_path(self, key: str) -> str:
        """Get the path for metadata file"""
        key_hash = self._get_hash(key)
        return os.path.join(self.metadata_dir, f"{key_hash}.json")
    
    def _get_tag_path(self, tag: str) -> str:
        """Get the path for tag file"""
        tag_hash = self._get_hash(tag)
        return os.path.join(self.tag_dir, f"{tag_hash}.json")
    
    def get(self, key: str) -> Optional[T]:
        """
        Get a value from the cache
        
        Args:
            key: Cache key
            
        Returns:
            Optional[T]: The cached value, or None if not found or expired
        """
        data_path = self._get_data_path(key)
        metadata_path = self._get_metadata_path(key)
        
        # Check if files exist
        if not os.path.exists(data_path) or not os.path.exists(metadata_path):
            return None
        
        try:
            # Read metadata
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            
            # Check if expired
            if "expiry" in metadata and metadata["expiry"] is not None:
                if time.time() > metadata["expiry"]:
                    # Expired, delete files
                    self.delete(key)
                    return None
            
            # Read data
            with open(data_path, "rb") as f:
                data = pickle.load(f)
            
            # Update access metadata
            metadata["accessed_at"] = time.time()
            metadata["access_count"] = metadata.get("access_count", 0) + 1
            
            with open(metadata_path, "w") as f:
                json.dump(metadata, f)
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting value from disk cache: {str(e)}")
            return None
    
    def set(self, key: str, value: T, ttl: Optional[int] = None, tags: Optional[List[str]] = None) -> bool:
        """
        Set a value in the cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL in seconds (defaults to instance TTL)
            tags: Optional tags for tag-based invalidation
            
        Returns:
            bool: True if the value was cached, False otherwise
        """
        data_path = self._get_data_path(key)
        metadata_path = self._get_metadata_path(key)
        
        try:
            # Calculate expiry
            expiry = time.time() + (ttl if ttl is not None else self.default_ttl) if ttl != 0 else None
            
            # Write data
            with open(data_path, "wb") as f:
                pickle.dump(value, f)
            
            # Write metadata
            metadata = {
                "key": key,
                "created_at": time.time(),
                "accessed_at": time.time(),
                "access_count": 0,
                "expiry": expiry,
                "tags": tags or []
            }
            
            with open(metadata_path, "w") as f:
                json.dump(metadata, f)
            
            # Update tag indexes
            for tag in tags or []:
                tag_path = self._get_tag_path(tag)
                
                try:
                    # Read existing tag index
                    if os.path.exists(tag_path):
                        with open(tag_path, "r") as f:
                            tag_data = json.load(f)
                    else:
                        tag_data = {"keys": []}
                    
                    # Add key if not already present
                    if key not in tag_data["keys"]:
                        tag_data["keys"].append(key)
                    
                    # Write updated tag index
                    with open(tag_path, "w") as f:
                        json.dump(tag_data, f)
                        
                except Exception as e:
                    logger.error(f"Error updating tag index for {tag}: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting value in disk cache: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if the value was deleted, False otherwise
        """
        data_path = self._get_data_path(key)
        metadata_path = self._get_metadata_path(key)
        
        try:
            # Check if metadata exists
            if os.path.exists(metadata_path):
                # Read metadata to get tags
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                
                # Remove key from tag indexes
                for tag in metadata.get("tags", []):
                    tag_path = self._get_tag_path(tag)
                    
                    if os.path.exists(tag_path):
                        try:
                            # Read tag index
                            with open(tag_path, "r") as f:
                                tag_data = json.load(f)
                            
                            # Remove key from index
                            if key in tag_data["keys"]:
                                tag_data["keys"].remove(key)
                            
                            # Write updated tag index or delete if empty
                            if tag_data["keys"]:
                                with open(tag_path, "w") as f:
                                    json.dump(tag_data, f)
                            else:
                                os.remove(tag_path)
                                
                        except Exception as e:
                            logger.error(f"Error updating tag index for {tag}: {str(e)}")
            
            # Delete files
            if os.path.exists(data_path):
                os.remove(data_path)
                
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
                
            return True
            
        except Exception as e:
            logger.error(f"Error deleting value from disk cache: {str(e)}")
            return False
    
    def clear(self):
        """Clear the cache"""
        try:
            # Delete all files in cache directories
            for dir_path in [self.data_dir, self.metadata_dir, self.tag_dir]:
                for filename in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing disk cache: {str(e)}")
            return False
    
    def invalidate_by_tag(self, tag: str) -> int:
        """
        Invalidate all entries with a specific tag
        
        Args:
            tag: Tag to invalidate
            
        Returns:
            int: Number of entries invalidated
        """
        tag_path = self._get_tag_path(tag)
        
        try:
            # Check if tag index exists
            if not os.path.exists(tag_path):
                return 0
            
            # Read tag index
            with open(tag_path, "r") as f:
                tag_data = json.load(f)
            
            keys = tag_data.get("keys", [])
            count = 0
            
            # Delete each key
            for key in keys:
                if self.delete(key):
                    count += 1
            
            # Delete tag index
            os.remove(tag_path)
            
            return count
            
        except Exception as e:
            logger.error(f"Error invalidating by tag in disk cache: {str(e)}")
            return 0
    
    def invalidate_by_prefix(self, prefix: str) -> int:
        """
        Invalidate all entries with keys starting with a specific prefix
        
        Args:
            prefix: Key prefix to invalidate
            
        Returns:
            int: Number of entries invalidated
        """
        try:
            count = 0
            keys_to_delete = []
            
            # Find all keys with this prefix by scanning metadata
            for filename in os.listdir(self.metadata_dir):
                metadata_path = os.path.join(self.metadata_dir, filename)
                
                if os.path.isfile(metadata_path):
                    try:
                        with open(metadata_path, "r") as f:
                            metadata = json.load(f)
                            
                        key = metadata.get("key", "")
                        
                        if key.startswith(prefix):
                            keys_to_delete.append(key)
                            
                    except Exception as e:
                        logger.error(f"Error reading metadata file {filename}: {str(e)}")
            
            # Delete all matching keys
            for key in keys_to_delete:
                if self.delete(key):
                    count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Error invalidating by prefix in disk cache: {str(e)}")
            return 0
    
    def _cleanup_loop(self):
        """Background thread for cleaning up expired cache entries"""
        cleanup_interval = 300  # 5 minutes
        
        while self.running:
            try:
                # Check for expired entries
                self._cleanup_expired()
                
            except Exception as e:
                logger.error(f"Error in disk cache cleanup loop: {str(e)}")
            
            # Sleep for cleanup interval
            for _ in range(cleanup_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def _cleanup_expired(self):
        """Clean up expired cache entries"""
        now = time.time()
        expired_count = 0
        
        # Scan metadata files for expired entries
        for filename in os.listdir(self.metadata_dir):
            if not self.running:
                break
                
            metadata_path = os.path.join(self.metadata_dir, filename)
            
            if os.path.isfile(metadata_path):
                try:
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                    
                    # Check if expired
                    if "expiry" in metadata and metadata["expiry"] is not None:
                        if now > metadata["expiry"]:
                            # Delete the entry
                            key = metadata.get("key", "")
                            if key and self.delete(key):
                                expired_count += 1
                                
                except Exception as e:
                    logger.error(f"Error checking expiry for {filename}: {str(e)}")
        
        if expired_count > 0:
            logger.debug(f"Cleaned up {expired_count} expired cache entries")

class CacheManager:
    """
    Cache manager for the TerraFlow platform
    
    This class provides a multi-level caching system with intelligent invalidation.
    """
    
    def __init__(self,
                memory_cache_size: int = 10000,
                memory_strategy: CacheStrategy = CacheStrategy.LRU,
                redis_client=None,
                redis_prefix: str = "terraflow:cache:",
                redis_ttl: int = 3600,
                disk_cache_dir: str = "data/cache",
                disk_ttl: int = 86400):
        """
        Initialize a new cache manager
        
        Args:
            memory_cache_size: Maximum number of entries in memory cache
            memory_strategy: Cache invalidation strategy for memory cache
            redis_client: Redis client instance (None to disable Redis cache)
            redis_prefix: Key prefix for Redis keys
            redis_ttl: Default TTL for Redis cache in seconds
            disk_cache_dir: Directory for disk cache files
            disk_ttl: Default TTL for disk cache in seconds
        """
        # Create cache instances
        self.memory_cache = MemoryCache(max_size=memory_cache_size, strategy=memory_strategy)
        self.redis_cache = RedisCache(redis_client, prefix=redis_prefix, ttl=redis_ttl) if redis_client else None
        self.disk_cache = DiskCache(cache_dir=disk_cache_dir, ttl=disk_ttl)
        
        # Cache configuration
        self.default_ttl = {
            CacheLevel.L1: 600,  # 10 minutes
            CacheLevel.L2: redis_ttl,
            CacheLevel.L3: disk_ttl
        }
    
    def get(self, key: str, level: Optional[CacheLevel] = None) -> Optional[Any]:
        """
        Get a value from the cache
        
        Args:
            key: Cache key
            level: Optional specific cache level to get from
            
        Returns:
            Optional[Any]: The cached value, or None if not found
        """
        # If level is specified, get from that level only
        if level:
            return self._get_from_level(key, level)
        
        # Check memory cache first (L1)
        value = self.memory_cache.get(key)
        if value is not None:
            return value
        
        # Check Redis cache next (L2)
        if self.redis_cache:
            value = self.redis_cache.get(key)
            if value is not None:
                # Propagate to memory cache
                self.memory_cache.set(key, value)
                return value
        
        # Check disk cache last (L3)
        value = self.disk_cache.get(key)
        if value is not None:
            # Propagate to memory cache and Redis cache
            self.memory_cache.set(key, value)
            if self.redis_cache:
                self.redis_cache.set(key, value)
            return value
        
        return None
    
    def _get_from_level(self, key: str, level: CacheLevel) -> Optional[Any]:
        """
        Get a value from a specific cache level
        
        Args:
            key: Cache key
            level: Cache level to get from
            
        Returns:
            Optional[Any]: The cached value, or None if not found
        """
        if level == CacheLevel.L1:
            return self.memory_cache.get(key)
        elif level == CacheLevel.L2 and self.redis_cache:
            return self.redis_cache.get(key)
        elif level == CacheLevel.L3:
            return self.disk_cache.get(key)
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[Dict[CacheLevel, int]] = None,
          tags: Optional[List[str]] = None, levels: Optional[List[CacheLevel]] = None) -> bool:
        """
        Set a value in the cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL in seconds for each level
            tags: Optional tags for tag-based invalidation
            levels: Optional specific cache levels to set in
            
        Returns:
            bool: True if the value was cached, False otherwise
        """
        # Default TTL and levels
        if ttl is None:
            ttl = self.default_ttl.copy()
            
        if levels is None:
            levels = [CacheLevel.L1, CacheLevel.L2, CacheLevel.L3]
        
        success = True
        
        # Set in memory cache (L1)
        if CacheLevel.L1 in levels:
            level_ttl = ttl.get(CacheLevel.L1, self.default_ttl[CacheLevel.L1])
            if not self.memory_cache.set(key, value, level_ttl, tags):
                success = False
        
        # Set in Redis cache (L2)
        if CacheLevel.L2 in levels and self.redis_cache:
            level_ttl = ttl.get(CacheLevel.L2, self.default_ttl[CacheLevel.L2])
            if not self.redis_cache.set(key, value, level_ttl, tags):
                success = False
        
        # Set in disk cache (L3)
        if CacheLevel.L3 in levels:
            level_ttl = ttl.get(CacheLevel.L3, self.default_ttl[CacheLevel.L3])
            if not self.disk_cache.set(key, value, level_ttl, tags):
                success = False
        
        return success
    
    def delete(self, key: str, levels: Optional[List[CacheLevel]] = None) -> bool:
        """
        Delete a value from the cache
        
        Args:
            key: Cache key
            levels: Optional specific cache levels to delete from
            
        Returns:
            bool: True if the value was deleted, False otherwise
        """
        if levels is None:
            levels = [CacheLevel.L1, CacheLevel.L2, CacheLevel.L3]
        
        success = True
        
        # Delete from memory cache (L1)
        if CacheLevel.L1 in levels:
            if not self.memory_cache.delete(key):
                success = False
        
        # Delete from Redis cache (L2)
        if CacheLevel.L2 in levels and self.redis_cache:
            if not self.redis_cache.delete(key):
                success = False
        
        # Delete from disk cache (L3)
        if CacheLevel.L3 in levels:
            if not self.disk_cache.delete(key):
                success = False
        
        return success
    
    def clear(self, levels: Optional[List[CacheLevel]] = None):
        """
        Clear the cache
        
        Args:
            levels: Optional specific cache levels to clear
        """
        if levels is None:
            levels = [CacheLevel.L1, CacheLevel.L2, CacheLevel.L3]
        
        # Clear memory cache (L1)
        if CacheLevel.L1 in levels:
            self.memory_cache.clear()
        
        # Clear Redis cache (L2)
        if CacheLevel.L2 in levels and self.redis_cache:
            self.redis_cache.clear()
        
        # Clear disk cache (L3)
        if CacheLevel.L3 in levels:
            self.disk_cache.clear()
    
    def invalidate_by_tag(self, tag: str, levels: Optional[List[CacheLevel]] = None) -> int:
        """
        Invalidate all entries with a specific tag
        
        Args:
            tag: Tag to invalidate
            levels: Optional specific cache levels to invalidate
            
        Returns:
            int: Number of entries invalidated
        """
        if levels is None:
            levels = [CacheLevel.L1, CacheLevel.L2, CacheLevel.L3]
        
        count = 0
        
        # Invalidate in memory cache (L1)
        if CacheLevel.L1 in levels:
            count += self.memory_cache.invalidate_by_tag(tag)
        
        # Invalidate in Redis cache (L2)
        if CacheLevel.L2 in levels and self.redis_cache:
            count += self.redis_cache.invalidate_by_tag(tag)
        
        # Invalidate in disk cache (L3)
        if CacheLevel.L3 in levels:
            count += self.disk_cache.invalidate_by_tag(tag)
        
        return count
    
    def invalidate_by_prefix(self, prefix: str, levels: Optional[List[CacheLevel]] = None) -> int:
        """
        Invalidate all entries with keys starting with a specific prefix
        
        Args:
            prefix: Key prefix to invalidate
            levels: Optional specific cache levels to invalidate
            
        Returns:
            int: Number of entries invalidated
        """
        if levels is None:
            levels = [CacheLevel.L1, CacheLevel.L2, CacheLevel.L3]
        
        count = 0
        
        # Invalidate in memory cache (L1)
        if CacheLevel.L1 in levels:
            count += self.memory_cache.invalidate_by_prefix(prefix)
        
        # Invalidate in Redis cache (L2)
        if CacheLevel.L2 in levels and self.redis_cache:
            count += self.redis_cache.invalidate_by_prefix(prefix)
        
        # Invalidate in disk cache (L3)
        if CacheLevel.L3 in levels:
            count += self.disk_cache.invalidate_by_prefix(prefix)
        
        return count
    
    def stop(self):
        """Stop cache manager and all background threads"""
        self.disk_cache.stop()
        
# Decorators for easy caching

def cached(key_prefix: str = "", ttl: Optional[Dict[CacheLevel, int]] = None,
         tags: Optional[List[str]] = None, levels: Optional[List[CacheLevel]] = None,
         cache_manager=None):
    """
    Decorator for caching function results
    
    Args:
        key_prefix: Prefix for cache keys
        ttl: Optional TTL in seconds for each level
        tags: Optional tags for tag-based invalidation
        levels: Optional specific cache levels to use
        cache_manager: Optional specific cache manager to use
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache manager
            cm = cache_manager
            if cm is None:
                # Try to get cache manager from global context
                import infrastructure.data.context as context
                cm = getattr(context, "cache_manager", None)
                
                if cm is None:
                    # Fall back to function result
                    return func(*args, **kwargs)
            
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            
            # Add args to key
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))
            
            # Add kwargs to key (in sorted order for consistency)
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float, bool)):
                    key_parts.append(f"{k}={v}")
            
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = cm.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = func(*args, **kwargs)
            
            # Cache result
            cm.set(cache_key, result, ttl=ttl, tags=tags, levels=levels)
            
            return result
        return wrapper
    return decorator