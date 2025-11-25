import time
from typing import Optional, Dict, Any
from config import settings

class SimpleCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() < entry["expires_at"]:
                return entry["value"]
            else:
                # Expired, remove it
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with TTL"""
        if ttl is None:
            ttl = settings.cache_ttl
        
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl
        }
    
    def clear(self):
        """Clear all cache"""
        self._cache.clear()
    
    def delete(self, key: str):
        """Delete specific key from cache"""
        if key in self._cache:
            del self._cache[key]

# Global cache instance
cache = SimpleCache()
