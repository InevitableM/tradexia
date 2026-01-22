"""Main ADK Runner configuration and management."""
from google.adk import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from typing import Optional
from loguru import logger


class MainRunner:
    """Main runner with shared services for all agents."""
    
    def __init__(self, app_name: str = 'tradexia'):
        """Initialize main runner with shared services.
        
        Args:
            app_name: Application name for the runner
        """
        # Initialize shared services for all agents
        self.artifact_service = InMemoryArtifactService()
        self.session_service = InMemorySessionService()
        self.memory_service = InMemoryMemoryService()
        self.app_name = app_name
        
        logger.info(f"Main runner initialized with app_name: {app_name}")
    
    def create_runner(self, agent, app_name: Optional[str] = None):
        """Create a runner instance with shared services.
        
        Args:
            agent: The agent to run
            app_name: Optional app name override
            
        Returns:
            Runner instance
        """
        return Runner(
            app_name=app_name or self.app_name,
            agent=agent,
            artifact_service=self.artifact_service,
            session_service=self.session_service,
            memory_service=self.memory_service,
        )


# Global main runner instance
_main_runner: Optional[MainRunner] = None


def get_main_runner(app_name: str = 'tradexia') -> MainRunner:
    """Get or create the main runner instance.
    
    Args:
        app_name: Application name
        
    Returns:
        MainRunner instance
    """
    global _main_runner
    if _main_runner is None:
        _main_runner = MainRunner(app_name=app_name)
    return _main_runner
