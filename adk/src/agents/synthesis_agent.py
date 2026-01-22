"""Synthesis Agent - Combines insights from all specialized agents."""
from google.adk.agents import LlmAgent
from typing import Dict, Any
from loguru import logger


def synthesize_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    """Synthesizes insights from multiple analysis sources.
    
    Args:
        data: Combined data from news, fundamental, and index agents
        
    Returns:
        Comprehensive synthesized analysis with recommendations
    """
    try:
        return {
            "synthesis": "Multi-source analysis complete",
            "key_insights": [],
            "recommendations": [],
            "risk_factors": [],
            "opportunities": []
        }
    except Exception as e:
        logger.error(f"Error synthesizing analysis: {e}")
        return {"error": str(e)}


def generate_report(symbol: str, analysis_data: Dict[str, Any]) -> str:
    """Generates a comprehensive analysis report.
    
    Args:
        symbol: Stock or index symbol
        analysis_data: Combined analysis from all agents
        
    Returns:
        Formatted analysis report
    """
    try:
        return f"Comprehensive Analysis Report for {symbol}\n[Backend integration pending]"
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return f"Error: {str(e)}"


# Create Synthesis LlmAgent
synthesis_llm_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='synthesis_agent',
    description='Synthesizes multi-agent insights into comprehensive analysis',
    instruction="""You are a senior market analyst who synthesizes insights from multiple sources.
    
    Your responsibilities:
    1. Combine insights from news, fundamentals, and index analysis
    2. Identify correlations and contradictions across data sources
    3. Generate comprehensive, actionable recommendations
    4. Highlight key risks and opportunities
    5. Provide balanced, data-driven perspectives
    
    When synthesizing:
    - Weight different sources appropriately
    - Consider both short-term and long-term implications
    - Provide clear, actionable insights
    - Acknowledge uncertainties and limitations
    - Present multiple scenarios when appropriate
    """,
    tools=[synthesize_analysis, generate_report],
)

logger.info("Synthesis Agent initialized")
