"""Redis cache client for fast data access."""
import redis
import json
from typing import Optional, Any
from loguru import logger
from ..config import get_settings


class CacheClient:
    """Redis cache client for reading cached data."""
    
    def __init__(self):
        """Initialize Redis connection."""
        settings = get_settings()
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password if settings.redis_password else None,
            db=settings.redis_db,
            decode_responses=True
        )
        logger.info("Redis cache client initialized")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with a TTL in seconds."""
        try:
            self.client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def get_stock_data(self, symbol: str) -> Optional[dict]:
        """Get cached stock data."""
        return self.get(f"stock:{symbol}")

    def set_screener_data(self, symbol: str, data: dict, ttl: int = 3600) -> bool:
        """Cache screener.in fundamental data for a symbol."""
        return self.set(f"screener:{symbol}", data, ttl)
    
    def get_news(self, symbol: str, limit: int = 10) -> Optional[list]:
        """Get cached news for a symbol."""
        return self.get(f"news:{symbol}:{limit}")
    
    def get_index_data(self, index_name: str) -> Optional[dict]:
        """Get cached index data."""
        return self.get(f"index:{index_name}")
    
    def get_sentiment(self, symbol: str) -> Optional[dict]:
        """Get cached sentiment data."""
        return self.get(f"sentiment:{symbol}")
    
    def health_check(self) -> bool:
        """Check if Redis is available."""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global cache client instance
_cache_client: Optional[CacheClient] = None


def get_cache_client() -> CacheClient:
    """Get or create cache client instance."""
    global _cache_client
    if _cache_client is None:
        _cache_client = CacheClient()
    return _cache_client
