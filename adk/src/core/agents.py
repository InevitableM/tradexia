"""Agent factory functions for creating different types of agents."""
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from typing import List, Optional, Callable, Any
from loguru import logger


def create_llm_agent(
    name: str,
    model: str = 'gemini-2.5-flash',
    description: str = '',
    instruction: str = '',
    tools: Optional[List[Callable]] = None,
    sub_agents: Optional[List[Any]] = None,
    output_key: Optional[str] = None,
) -> LlmAgent:
    """Create an LLM agent with standard configuration.
    
    Args:
        name: Agent name
        model: Model to use
        description: Agent description
        instruction: System instruction for the agent
        tools: List of tools available to the agent
        sub_agents: List of sub-agents
        output_key: Key to store agent output in session state
        
    Returns:
        LlmAgent instance
    """
    logger.info(f"Creating LLM agent: {name}")
    
    return LlmAgent(
        name=name,
        model=model,
        description=description,
        instruction=instruction,
        tools=tools or [],
        sub_agents=sub_agents or [],
        output_key=output_key,
    )


def create_parallel_agent(
    name: str,
    sub_agents: List[Any],
    description: str = '',
) -> ParallelAgent:
    """Create a parallel agent that executes sub-agents concurrently.
    
    Args:
        name: Agent name
        sub_agents: List of agents to execute in parallel
        description: Agent description
        
    Returns:
        ParallelAgent instance
    """
    logger.info(f"Creating Parallel agent: {name} with {len(sub_agents)} sub-agents")
    
    return ParallelAgent(
        name=name,
        description=description,
        sub_agents=sub_agents,
    )


def create_sequential_agent(
    name: str,
    sub_agents: List[Any],
    description: str = '',
) -> SequentialAgent:
    """Create a sequential agent that executes sub-agents in order.
    
    Args:
        name: Agent name
        sub_agents: List of agents to execute sequentially
        description: Agent description
        
    Returns:
        SequentialAgent instance
    """
    logger.info(f"Creating Sequential agent: {name} with {len(sub_agents)} sub-agents")
    
    return SequentialAgent(
        name=name,
        description=description,
        sub_agents=sub_agents,
    )
