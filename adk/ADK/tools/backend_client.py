"""Backend API client for making requests to the Node backend service."""

import httpx
from typing import Optional, Dict, Any
from loguru import logger
from ..config import get_settings


class BackendClient:
    """HTTP client for Node backend API calls."""

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.backend_api_url

    def _headers(self, access_token: Optional[str] = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    async def save_conversation(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        access_token: str,
    ) -> Optional[Dict[str, Any]]:
        """Persist a user+assistant message pair to the Node backend."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/conversations",
                    json={
                        "sessionId": session_id,
                        "userMessage": user_message,
                        "assistantMessage": assistant_message,
                    },
                    headers=self._headers(access_token),
                    timeout=10.0,
                )
                response.raise_for_status()
                logger.info(f"[backend_client] conversation saved session_id={session_id}")
                return response.json()
        except Exception as e:
            logger.error(f"[backend_client] save_conversation failed: {e}")
            return None


# Global backend client instance
_backend_client: Optional[BackendClient] = None


def get_backend_client() -> BackendClient:
    """Get or create backend client instance."""
    global _backend_client
    if _backend_client is None:
        _backend_client = BackendClient()
    return _backend_client
