"""Root agent entry point for ADK web UI."""
from loguru import logger
from .agents.orchestrator import orchestrator_llm_agent, get_orchestrator

# Initialize the orchestrator instance to set up shared services
# This ensures _shared_services is populated when root_agent is used
logger.info("Initializing orchestrator for ADK web UI...")
_orchestrator = get_orchestrator()
logger.info(f"Orchestrator initialized successfully")

# Export the orchestrator LlmAgent as root_agent
# This ensures ADK web UI uses the same orchestrator configuration
root_agent = orchestrator_llm_agent

