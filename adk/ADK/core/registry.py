"""Agent Registry - Central registry for all available agents."""
from typing import Dict, Any, Callable
from loguru import logger


class AgentRegistry:
    """Registry for managing available agent factories."""

    def __init__(self):
        """Initialize empty agent registry."""
        self._factories: Dict[str, Callable] = {}
        logger.info("Agent registry initialized")

    def register(self, name: str, factory: Callable) -> None:
        """Register an agent factory function.

        Args:
            name:    Agent name (used for lookup)
            factory: Zero-argument callable that returns a fresh LlmAgent instance
        """
        self._factories[name] = factory
        logger.info(f"Registered agent factory: {name}")

    def create(self, name: str) -> Any:
        """Create a fresh agent instance from its factory.

        Each call returns a brand-new LlmAgent with no parent set,
        preventing ADK re-parenting errors when agents are reused
        across different wrapper combinations.

        Args:
            name: Agent name

        Returns:
            Fresh LlmAgent instance, or None if name not found
        """
        factory = self._factories.get(name)
        if factory is None:
            return None
        return factory()

    def create_multiple(self, names: list) -> Dict[str, Any]:
        """Create fresh instances for multiple agents.

        Args:
            names: List of agent names

        Returns:
            Dict mapping names to fresh LlmAgent instances
        """
        return {name: self.create(name) for name in names if name in self._factories}

    def get(self, name: str) -> Any:
        """Return the factory callable for an agent (not an instance).

        Prefer create() when you need an agent to run.
        """
        return self._factories.get(name)

    def get_multiple(self, names: list) -> Dict[str, Any]:
        """Return factory callables for multiple agents.

        Prefer create_multiple() when you need agents to run.
        """
        return {name: self._factories.get(name) for name in names if name in self._factories}

    def list_agents(self) -> list:
        """List all registered agent names."""
        return list(self._factories.keys())

    def clear(self) -> None:
        """Clear all registered factories."""
        self._factories.clear()
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
