"""Main entry point for Tradexia ADK agents."""
import asyncio
import os
from loguru import logger
import sys
from .config import get_settings
from .agents.orchestrator import get_orchestrator


def setup_logging():
    """Configure logging for the application."""
    settings = get_settings()
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.log_level
    )


async def main():
    """Main entry point for testing the orchestrator."""
    setup_logging()
    
    # Set Google API key as environment variable
    settings = get_settings()
    os.environ['GOOGLE_API_KEY'] = settings.google_api_key
    
    logger.info("Starting Tradexia ADK Agent System")
    
    # Initialize orchestrator
    orchestrator = get_orchestrator()
    
    # Health check
    health = orchestrator.health_check()
    logger.info(f"System health: {health}")
    
    # Test query
    test_query = "What are the top performing stocks in Nifty50 today?"
    logger.info(f"Test Query: {test_query}")
    
    response = await orchestrator.analyze(test_query)
    logger.info(f"Response: {response}")


if __name__ == "__main__":
    asyncio.run(main())
