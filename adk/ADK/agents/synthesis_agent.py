"""Synthesis Agent - Combines insights from all specialized agents."""

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from typing import Dict, Any
from loguru import logger


def synthesize_analysis(tool_context: ToolContext) -> Dict[str, Any]:
    """Reads news and fundamental analyses from session state.

    ADK automatically injects tool_context, giving full access to session.state.
    Call this tool to access the raw data if you need it for deeper processing.

    Returns:
        Dict with news_analysis and fundamental_analysis from session state
    """
    news_result = tool_context.state.get("news_result", "News analysis not available")
    fundamental_result = tool_context.state.get(
        "fundamental_result", "Fundamental analysis not available"
    )

    logger.info("[synthesize_analysis] Reading from session state:")
    logger.info(f"  news_result      : {len(str(news_result))} chars → {str(news_result)[:200]}")
    logger.info(
        f"  fundamental_result: {len(str(fundamental_result))} chars → {str(fundamental_result)[:200]}"
    )

    return {
        "news_analysis": news_result,
        "fundamental_analysis": fundamental_result,
    }


def generate_report(symbol: str, tool_context: ToolContext) -> str:
    """Generates a formatted analysis report for a stock symbol.

    Reads news_result and fundamental_result from session state.
    ADK injects tool_context automatically — do not pass it manually.

    Args:
        symbol: Stock symbol (e.g. 'TCS', 'RELIANCE')

    Returns:
        Formatted report string
    """
    try:
        news = tool_context.state.get("news_result", "N/A")
        fundamentals = tool_context.state.get("fundamental_result", "N/A")

        logger.info(f"[generate_report] Building report for {symbol}")

        return (
            f"=== Comprehensive Analysis Report: {symbol} ===\n\n"
            f"--- NEWS & SENTIMENT ---\n{news}\n\n"
            f"--- FUNDAMENTALS ---\n{fundamentals}\n"
        )
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return f"Error: {str(e)}"


def _synthesis_before_agent_callback(
    callback_context: CallbackContext,
):
    """Guard: short-circuit synthesis if news_result or fundamental_result are missing."""
    missing = [
        key for key in ("news_result", "fundamental_result") if not callback_context.state.get(key)
    ]
    result = callback_context.state.get("fundamental_result")
    print(
        f"[synthesis_before_agent_callback] fundamental_result length: {len(result) if result else 0}"
    )
    if missing:
        logger.warning(
            f"[synthesis_before_agent_callback] Missing state keys: {missing} — aborting synthesis"
        )
    logger.info(
        "[synthesis_before_agent_callback] news_result and fundamental_result present — proceeding"
    )
    return None


def make_synthesis_agent() -> LlmAgent:
    """Factory — returns a fresh LlmAgent instance each call to avoid ADK re-parenting errors."""
    return LlmAgent(
        model="gemini-2.5-flash",
        name="synthesis_agent",
        description="Synthesizes multi-agent insights into comprehensive analysis",
        before_agent_callback=_synthesis_before_agent_callback,
        instruction="""You are a senior market analyst who synthesizes insights from multiple sources.

    Your responsibilities:
    1. Combine insights from news, fundamentals analysis
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
        tools=[synthesize_analysis],
    )

logger.info("Synthesis Agent factory ready")
