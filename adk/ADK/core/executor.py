"""Agent Executor - Dynamic execution of agents in parallel or sequential mode."""
from typing import List, Dict, Any, Optional
from google.genai import types
from google.adk.events import Event, EventActions
import asyncio
from loguru import logger
from .runner import get_main_runner
from .agents import create_parallel_agent, create_sequential_agent
from .registry import get_agent_registry


async def update_session_state(session_service, session, state_delta: dict):
    """Update session state from outside an agent using ADK's append_event.

    Direct mutation (session.state["x"] = v) does NOT persist to the session
    service. This function uses append_event with a state_delta, which IS
    the proper ADK mechanism for external state updates.

    Args:
        session_service: The ADK session service instance
        session: The current Session object
        state_delta: Dict of key-value pairs to set in session state

    Example:
        await update_session_state(runner.session_service, session, {
            "news_result": "TCS news analysis...",
            "fundamental_result": "P/E: 24, ROE: 40%",
        })
    """
    event = Event(
        invocation_id=session.id,
        author="executor",
        actions=EventActions(state_delta=state_delta),
    )
    await session_service.append_event(session, event)
    logger.info(f"State updated via append_event: keys={list(state_delta.keys())}")


class AgentExecutor:
    """Executes agents dynamically based on mode."""
    
    def __init__(self):
        """Initialize agent executor."""
        self.main_runner = get_main_runner()
        self.registry = get_agent_registry()
        # Cache wrapper agents and runners to avoid re-parenting singleton sub-agents
        self._wrapper_agents: Dict[str, Any] = {}
        self._runners: Dict[str, Any] = {}
        logger.info("Agent executor initialized")
    
    def _get_or_create_wrapper(self, mode: str, agent_names: List[str], agents: list):
        """Get a cached wrapper agent+runner, or create one if it doesn't exist yet.
        
        ADK sets a parent pointer on each sub-agent when it's added to a
        ParallelAgent/SequentialAgent. Re-creating the wrapper with the same
        singleton sub-agents on every request raises:
            'Agent X already has a parent agent'
        
        We avoid this by creating each (mode, frozenset(agent_names)) combination
        exactly once and reusing it for all subsequent requests.

        IMPORTANT: All runners use the same app_name ("tradexia_executor") so that
        parallel and sequential executions share the same session namespace.
        This allows session.state written by news/fundamental agents to be read
        by synthesis when it runs in a subsequent call.
        """
        # Use a stable cache key: mode + sorted agent names
        cache_key = f"{mode}::{':'.join(sorted(agent_names))}"
        
        if cache_key not in self._wrapper_agents:
            # All runners share the same app_name so sessions are in the same namespace
            app_name = "tradexia_executor"
            logger.info(f"Creating new {mode} wrapper agent for key: {cache_key}")
            
            if mode == "parallel":
                wrapper_agent = create_parallel_agent(
                    name=f"parallel_executor",
                    sub_agents=agents,
                    description=f"Executes {len(agents)} agents in parallel"
                )
            else:  # sequential
                wrapper_agent = create_sequential_agent(
                    name=f"sequential_executor",
                    sub_agents=agents,
                    description=f"Executes {len(agents)} agents sequentially"
                )
            
            runner = self.main_runner.create_runner(
                agent=wrapper_agent,
                app_name=app_name
            )
            
            self._wrapper_agents[cache_key] = wrapper_agent
            self._runners[cache_key] = runner
        else:
            logger.info(f"Reusing cached {mode} wrapper agent for key: {cache_key}")
        
        return self._runners[cache_key]

    async def execute_agents(
        self,
        agent_names: List[str],
        query: str,
        mode: str = "parallel",
        session_id: Optional[str] = None,
        user_id: str = "default_user",
    ) -> Dict[str, Any]:
        """Execute multiple agents dynamically.
        
        Args:
            agent_names: List of agent names to execute
            query: Query to pass to agents
            mode: Execution mode - "parallel" or "sequential"
            session_id: Session ID for context sharing
            user_id: User ID
            
        Returns:
            Dict with results from all agents
        """
        try:
            logger.info(f"Executing agents {agent_names} in {mode} mode")
            
            # Get agents from registry
            agents_dict = self.registry.get_multiple(agent_names)
            
            # Check for missing agents
            missing = [name for name in agent_names if name not in agents_dict]
            if missing:
                logger.warning(f"Agents not found in registry: {missing}")
                return {
                    "error": f"Agents not found: {missing}",
                    "available_agents": self.registry.list_agents()
                }
            
            if mode not in ("parallel", "sequential"):
                return {"error": f"Invalid mode: {mode}. Use 'parallel' or 'sequential'"}
            
            agents = list(agents_dict.values())
            
            # Get or create the wrapper agent+runner (cached to avoid re-parenting)
            runner = self._get_or_create_wrapper(mode, agent_names, agents)
            
            # Get or create session
            if not session_id:
                import uuid
                session_id = str(uuid.uuid4())
            
            session = await runner.session_service.get_session(
                app_name=runner.app_name,
                user_id=user_id,
                session_id=session_id,
            )
        
            if not session:
                session = await runner.session_service.create_session(
                    app_name=runner.app_name,
                    user_id=user_id,
                    session_id=session_id,
                )
            
            # Create message content
            content = types.Content(role='user', parts=[types.Part(text=query)])
            
            # Execute agents
            logger.info(f"Running {mode} executor for query: {query}")
            results = {}
            event_count = 0

            async for event in runner.run_async(
                session_id=session.id,
                user_id=user_id,
                new_message=content
            ):
                event_count += 1
                logger.debug(
                    f"Event #{event_count} | author={getattr(event, 'author', '?')} "
                    f"is_final={event.is_final_response()} "
                    f"has_content={event.content is not None}"
                )
                # Collect results from events
                if event.is_final_response() and event.content and event.content.parts:
                    response_text = "".join(
                        part.text for part in event.content.parts
                        if hasattr(part, 'text') and part.text
                    )
                    results["response"] = response_text
                    logger.debug(f"Final response captured: {len(response_text)} chars")

            logger.info(f"Stream complete: {event_count} total events | agents={agent_names} state_keys={list(session.state.keys())}")

            # Also collect any state written by agents
            results["state"] = dict(session.state)
            results["mode"] = mode
            results["agents_executed"] = agent_names

            logger.info(f"{mode.capitalize()} execution completed for {len(agent_names)} agents", results)
            return results

        except Exception as e:
            import traceback
            logger.error(
                f"Error executing agents in {mode} mode | agents={agent_names} session_id={session_id}\n"
                f"Type : {type(e).__name__}\n"
                f"Error: {e}\n"
                f"{traceback.format_exc()}"
            )
            return {"error": str(e)}


# Global executor instance
_executor: Optional[AgentExecutor] = None


def get_agent_executor() -> AgentExecutor:
    """Get the global agent executor instance.
    
    Returns:
        AgentExecutor instance
    """
    global _executor
    if _executor is None:
        _executor = AgentExecutor()
    return _executor
