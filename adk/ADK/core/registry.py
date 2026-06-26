"""Agent Registry - Central registry for all available agents."""
from typing import Dict, Any
from loguru import logger


class AgentRegistry:
    """Registry for managing available agents."""
    
    def __init__(self):
        """Initialize empty agent registry."""
        self._agents: Dict[str, Any] = {}
        logger.info("Agent registry initialized")
    
    def register(self, name: str, agent: Any) -> None:
        """Register an agent.
        
        Args:
            name: Agent name (used for lookup)
            agent: Agent instance
        """
        self._agents[name] = agent
        logger.info(f"Registered agent: {name}")
    
    def get(self, name: str) -> Any:
        """Get an agent by name.
        
        Args:
            name: Agent name
            
        Returns:
            Agent instance or None if not found
        """
        return self._agents.get(name)
    
    def get_multiple(self, names: list) -> Dict[str, Any]:
        """Get multiple agents by names.
        
        Args:
            names: List of agent names
            
        Returns:
            Dict mapping names to agent instances
        """
        return {name: self._agents.get(name) for name in names if name in self._agents}
    
    def list_agents(self) -> list:
        """List all registered agent names.
        
        Returns:
            List of agent names
        """
        return list(self._agents.keys())
    
    def clear(self) -> None:
        """Clear all registered agents."""
        self._agents.clear()
        logger.info("Agent registry cleared")


# Global agent registry instance
_registry: AgentRegistry = None


def get_agent_registry() -> AgentRegistry:
    """Get the global agent registry instance.
    
    Returns:
        AgentRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
