"""Agent Executor - Dynamic execution of agents in parallel or sequential mode."""

from typing import List, Dict, Any, Optional
from google.genai import types
from loguru import logger
from .runner import get_main_runner
from .agents import create_parallel_agent, create_sequential_agent
from .registry import get_agent_registry


class AgentExecutor:
    """Executes agents dynamically based on mode."""

    def __init__(self):
        """Initialize agent executor."""
        self.main_runner = get_main_runner()
        self.registry = get_agent_registry()
        logger.info("Agent executor initialized")

    def _build_wrapper(self, mode: str, agent_names: List[str], agents: list):
        """Build a fresh wrapper agent and runner for this execution.

        Agents are created fresh from factories each call so ADK never sees a
        sub-agent that already has a parent — no re-parenting errors regardless
        of which combination is requested.

        All runners share app_name 'tradexia_executor' so session.state written
        by parallel agents is visible to sequential agents in the same turn.
        """
        app_name = "tradexia_executor"
        logger.info(f"Building {mode} wrapper for agents: {agent_names}")

        if mode == "parallel":
            wrapper_agent = create_parallel_agent(
                name="parallel_executor",
                sub_agents=agents,
                description=f"Executes {len(agents)} agents in parallel",
            )
        else:
            wrapper_agent = create_sequential_agent(
                name="sequential_executor",
                sub_agents=agents,
                description=f"Executes {len(agents)} agents sequentially",
            )

        return self.main_runner.create_runner(agent=wrapper_agent, app_name=app_name)

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

            # Create fresh agent instances from factories (prevents ADK re-parenting errors)
            agents_dict = self.registry.create_multiple(agent_names)

            # Check for missing agents
            missing = [name for name in agent_names if name not in agents_dict]
            if missing:
                logger.warning(f"Agents not found in registry: {missing}")
                return {
                    "error": f"Agents not found: {missing}",
                    "available_agents": self.registry.list_agents(),
                }

            if mode not in ("parallel", "sequential"):
                return {"error": f"Invalid mode: {mode}. Use 'parallel' or 'sequential'"}

            agents = list(agents_dict.values())

            # Build a fresh wrapper with fresh agent instances each call
            runner = self._build_wrapper(mode, agent_names, agents)

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
            content = types.Content(role="user", parts=[types.Part(text=query)])

            # Execute agents
            logger.info(f"Running {mode} executor for query: {query}")
            results = {}
            event_count = 0

            async for event in runner.run_async(
                session_id=session.id, user_id=user_id, new_message=content
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
                        part.text
                        for part in event.content.parts
                        if hasattr(part, "text") and part.text
                    )
                    results["response"] = response_text
                    logger.debug(f"Final response captured: {len(response_text)} chars")

            logger.info(
                f"Stream complete: {event_count} total events | agents={agent_names} state_keys={list(session.state.keys())}"
            )

            # Also collect any state written by agents
            results["state"] = dict(session.state)
            results["mode"] = mode
            results["agents_executed"] = agent_names

            logger.info(
                f"{mode.capitalize()} execution completed for {len(agent_names)} agents", results
            )
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
