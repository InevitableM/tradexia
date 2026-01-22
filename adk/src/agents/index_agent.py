"""Index Composition Agent - Analyzes index structure and constituent stocks."""
from google.adk.agents import LlmAgent
from typing import Dict, Any
from loguru import logger
from ..tools.backend_client import get_backend_client
from ..cache import get_cache_client


def get_index_composition(index_name: str) -> Dict[str, Any]:
    """Retrieves the composition and constituents of an index.
    
    Args:
        index_name: Index name (e.g., 'NIFTY50', 'BANKNIFTY')
        
    Returns:
        Index constituents, weightages, and sector distribution
    """
    try:
        cache = get_cache_client()
        
        # Try cache first
        cached_data = cache.get_index_data(index_name)
        if cached_data:
            logger.info(f"Index data for {index_name} found in cache")
            return cached_data
        
        # Placeholder for backend call
        return {
            "index": index_name,
            "constituents": [],
            "sector_distribution": {},
            "message": "Backend integration pending"
        }
    except Exception as e:
        logger.error(f"Error fetching index data for {index_name}: {e}")
        return {"error": str(e)}


def analyze_index_performance(index_name: str) -> Dict[str, Any]:
    """Analyzes overall index performance and top contributors.
    
    Args:
        index_name: Index name
        
    Returns:
        Performance analysis including top gainers/losers and contribution analysis
    """
    try:
        return {
            "index": index_name,
            "performance": {},
            "top_contributors": [],
            "top_losers": [],
            "message": "Backend integration pending"
        }
    except Exception as e:
        logger.error(f"Error analyzing index performance for {index_name}: {e}")
        return {"error": str(e)}


def get_sector_analysis(index_name: str) -> Dict[str, Any]:
    """Analyzes sector-wise performance within an index.
    
    Args:
        index_name: Index name
        
    Returns:
        Sector-wise breakdown and performance analysis
    """
    try:
        return {
            "index": index_name,
            "sector_performance": {},
            "sector_weights": {},
            "message": "Backend integration pending"
        }
    except Exception as e:
        logger.error(f"Error analyzing sectors for {index_name}: {e}")
        return {"error": str(e)}


# Create Index LlmAgent
index_llm_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='index_composition_agent',
    description='Analyzes index composition and performance',
    instruction="""You are an index analysis expert specializing in Indian stock market indices.
    
    Your responsibilities:
    1. Analyze index composition and constituent stocks
    2. Track weightages and rebalancing changes
    3. Identify top contributors and detractors to index movement
    4. Provide sector-wise breakdown and analysis
    5. Compare performance across different indices
    
    Use the available tools to fetch index data and analyze composition.
    Provide insights on how individual stocks impact overall index performance.
    Consider sector rotation and concentration risks.
    """,
    tools=[get_index_composition, analyze_index_performance, get_sector_analysis],
)

logger.info("Index Composition Agent initialized")
