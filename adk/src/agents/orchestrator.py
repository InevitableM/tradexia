"""Orchestrator Agent - Routes queries using dynamic multi-agent execution."""
from google.adk.agents import LlmAgent
from google.genai import types
from typing import Optional, List
import asyncio
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
from ..config import get_settings
from ..cache import get_cache_client
from ..tools.backend_client import get_backend_client
from ..core import get_agent_registry, get_agent_executor, get_main_runner

# Import sub-agent LlmAgent instances
from .news_agent import news_llm_agent
from .synthesis_agent import synthesis_llm_agent
from .fundamental_agent import fundamental_llm_agent
from .index_agent import index_llm_agent

# Thread pool for async execution in sync context
_thread_pool = ThreadPoolExecutor(max_workers=5, thread_name_prefix="agent-executor")

# Register all available agents
registry = get_agent_registry()
registry.register("news", news_llm_agent)
registry.register("fundamental", fundamental_llm_agent)

logger.info(f"Registered agents: {registry.list_agents()}")


def call_agents_parallel(agent_names: List[str], query: str) -> str:
    """Call multiple agents in parallel for independent analyses.
    
    Use this when agents can work independently without waiting for each other.
    Example: News + Fundamental + Index analysis can all run simultaneously.
    
    Args:
        agent_names: List of agent names to call (e.g., ["news", "fundamental", "index"])
        query: The analysis query to pass to all agents
        
    Returns:
        Combined results from all agents
    """
    try:
        logger.info(f"Calling agents in parallel: {agent_names} with query: {query}")
        
        executor = get_agent_executor()
        
        # Run async execution in thread pool to avoid event loop conflicts
        def run_async_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    executor.execute_agents(
                        agent_names=agent_names,
                        query=query,
                        mode="parallel"
                    )
                )
            finally:
                loop.close()
        
        future = _thread_pool.submit(run_async_in_thread)
        results = future.result(timeout=60)
        
        if "error" in results:
            return f"Error: {results['error']}"
        
        return results.get("response", "No response from agents")
        
    except Exception as e:
        logger.error(f"Error in parallel agent execution: {e}", exc_info=True)
        return f"Error calling agents: {str(e)}"


def call_agents_sequential(agent_names: List[str], query: str) -> str:
    """Call multiple agents sequentially when one depends on another's output.
    
    Use this when later agents need results from earlier agents.
    Example: First run analysis agents, then synthesis agent uses their results.
    
    Args:
        agent_names: List of agent names in execution order (e.g., ["news", "synthesis"])
        query: The analysis query to pass to agents
        
    Returns:
        Results from sequential execution
    """
    try:
        logger.info(f"Calling agents sequentially: {agent_names} with query: {query}")
        
        executor = get_agent_executor()
        
        # Run async execution in thread pool to avoid event loop conflicts
        def run_async_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    executor.execute_agents(
                        agent_names=agent_names,
                        query=query,
                        mode="sequential"
                    )
                )
            finally:
                loop.close()
        
        future = _thread_pool.submit(run_async_in_thread)
        results = future.result(timeout=60)
        
        if "error" in results:
            return f"Error: {results['error']}"
        
        return results.get("response", "No response from agents")
        
    except Exception as e:
        logger.error(f"Error in sequential agent execution: {e}", exc_info=True)
        return f"Error calling agents: {str(e)}"


# Create Orchestrator LlmAgent with dynamic agent calling tools
orchestrator_llm_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='orchestrator_agent',
    description='Main orchestrator for multi-agent stock analysis system with dynamic parallel/sequential execution',
    instruction="""You are the master orchestrator for a multi-agent financial analysis system.

Your role:
1. Understand user queries about stocks, indices, and markets
2. Intelligently decide which agents to call and how to execute them
3. Coordinate responses and provide coherent, comprehensive answers

Available Agents:
- news: News analysis and sentiment for stocks
- fundamental: Financial metrics, growth analysis, company fundamentals

Execution Strategies:

1. PARALLEL EXECUTION (use call_agents_parallel):
   - When agents work independently
   - Example: News + Fundamental can all analyze simultaneously
   - Faster execution for comprehensive analysis
   
2. SEQUENTIAL EXECUTION (use call_agents_sequential):
   - When later agents need earlier results
   - Example: [news, fundamental] 
   - Use when synthesis needs to combine multiple analyses

Decision Guidelines:
- Single topic (just news) → call_agents_parallel with ["news"]
- Comprehensive analysis → call_agents_parallel with ["news", "fundamental"], then call_agents_sequential with ["synthesis"] if needed
- Quick analysis → call_agents_parallel with relevant agents
- Deep analysis → parallel first, then sequential for synthesis

Always ensure the user gets complete, actionable insights.
""",
    tools=[call_agents_parallel, call_agents_sequential],
)

logger.info("Orchestrator Agent initialized with dynamic parallel/sequential execution")


class OrchestratorAgent:
    """Main orchestrator using dynamic multi-agent execution."""
    
    def __init__(self):
        """Initialize orchestrator with main runner."""
        self.cache = get_cache_client()
        self.backend = get_backend_client()
        
        # Use the shared main runner
        main_runner = get_main_runner()
        
        # Create runner for orchestrator using shared services
        self.runner = main_runner.create_runner(
            agent=orchestrator_llm_agent,
            app_name='tradexia_orchestrator'
        )
        
        logger.info("Orchestrator Agent initialized with dynamic multi-agent execution")
    
    def health_check(self) -> dict:
        """Health check for all components."""
        return {
            "orchestrator": "healthy",
            "cache": "healthy" if self.cache.health_check() else "unhealthy",
            "framework": "Google ADK",
            "registered_agents": registry.list_agents(),
            "execution_modes": ["parallel", "sequential"],
            "pattern": "Dynamic Multi-Agent Execution"
        }
    
    async def analyze(self, query: str, user_id: str = "default_user", session_id: Optional[str] = None) -> str:
        """Analyze a query using the orchestrator.
        
        The orchestrator LLM will automatically call sub-agents (via AgentTools) 
        when needed based on the query.
        """
        try:
            logger.info(f"Analyzing query: {query}")
            
            # Get or create session
            if not session_id:
                import uuid
                session_id = str(uuid.uuid4())
            
            session = await self.runner.session_service.get_session(
                app_name=self.runner.app_name,
                user_id=user_id,
                session_id=session_id,
            )
            
            if not session:
                session = await self.runner.session_service.create_session(
                    app_name=self.runner.app_name,
                    user_id=user_id,
                    session_id=session_id,
                )
            
            # Create message content
            content = types.Content(role='user', parts=[types.Part(text=query)])
            
            # Run agent - ADK automatically handles sub-agent calls via AgentTools
            response_text = ""
            async for event in self.runner.run_async(
                session_id=session.id,
                user_id=user_id,
                new_message=content
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    response_text = "".join(
                        part.text for part in event.content.parts 
                        if hasattr(part, 'text') and part.text
                    )
                    break
            
            return response_text if response_text else "No response generated"
            
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            return f"Error: {str(e)}"


# Global instance
_orchestrator: Optional[OrchestratorAgent] = None


def get_orchestrator() -> OrchestratorAgent:
    """Get or create orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator
