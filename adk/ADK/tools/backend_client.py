"""Backend API client for making requests to the backend service."""
import httpx
from typing import Optional, Dict, Any
from loguru import logger
from ..config import get_settings


class BackendClient:
    """HTTP client for backend API calls."""
    
    def __init__(self):
        """Initialize backend client."""
        settings = get_settings()
        self.base_url = settings.backend_api_url
        self.api_key = settings.backend_api_key
        self.headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    async def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch stock data from backend."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/stocks/{symbol}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return None
    
    async def get_news(self, symbol: str, limit: int = 10) -> Optional[list]:
        """Fetch news for a symbol from backend."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/news/{symbol}",
                    params={"limit": limit},
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return None
    
    async def get_index_data(self, index_name: str) -> Optional[Dict[str, Any]]:
        """Fetch index data from backend."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/indices/{index_name}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching index data for {index_name}: {e}")
            return None
    
    async def get_fundamental_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch fundamental data from backend."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/fundamentals/{symbol}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching fundamental data for {symbol}: {e}")
            return None


# Global backend client instance
_backend_client: Optional[BackendClient] = None


def get_backend_client() -> BackendClient:
    """Get or create backend client instance."""
    global _backend_client
    if _backend_client is None:
        _backend_client = BackendClient()
    return _backend_client
