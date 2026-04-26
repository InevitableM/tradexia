"""Fundamental Analysis Agent - Evaluates financial metrics and company fundamentals."""
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from typing import Dict, Any, Optional
from loguru import logger
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import threading
from ..tools.backend_client import get_backend_client
from ..cache import get_cache_client



def get_financial_metrics(symbol: str) -> Dict[str, Any]:
    """Retrieves key financial metrics for a stock.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        Dict containing P/E ratio, market cap, revenue, profit, etc.
    """
    try:
        cache = get_cache_client()
        
        # Try cache first
        cached_data = cache.get_stock_data(symbol)
        if cached_data:
            logger.info(f"Financial metrics for {symbol} found in cache")
            return cached_data
        
        # Placeholder for backend call
        return {
            "symbol": symbol,
            "message": "Backend integration pending",
            "metrics": {}
        }
    except Exception as e:
        logger.error(f"Error fetching metrics for {symbol}: {e}")
        return {"error": str(e)}


def analyze_growth_trends(symbol: str) -> Dict[str, Any]:
    """Analyzes sales growth, profit trends, and future projections.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Growth analysis including historical trends and projections
    """
    try:
        return {
            "symbol": symbol,
            "revenue_growth": None,
            "profit_growth": None,
            "projections": {},
            "message": "Backend integration pending"
        }
    except Exception as e:
        logger.error(f"Error analyzing growth for {symbol}: {e}")
        return {"error": str(e)}


def evaluate_company_plans(symbol: str) -> Dict[str, Any]:
    """Evaluates company's future plans, expansions, and strategic initiatives.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Analysis of company's strategic plans and initiatives
    """
    try:
        return {
            "symbol": symbol,
            "future_plans": [],
            "expansions": [],
            "strategic_initiatives": [],
            "message": "Backend integration pending"
        }
    except Exception as e:
        logger.error(f"Error evaluating plans for {symbol}: {e}")
        return {"error": str(e)}


def get_screener_data(symbol: str) -> Dict[str, Any]:
    """Scrapes comprehensive fundamental data for an Indian stock from Screener.in.
    
    Includes key ratios, quarterly results, profit & loss statements, 
    balance sheets, and cash flow data.
    
    Args:
        symbol: Stock symbol (e.g., 'TCS', 'RELIANCE')
        
    Returns:
        Dict containing key metrics and financial tables
    """
    try:
        url = f"https://www.screener.in/company/{symbol}/"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        logger.info(f"Scraping screener data for {symbol}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        data = {}

        # 1. TOP RATIOS (Key Metrics)
        ratios = soup.select("ul#top-ratios li")
        key_metrics = {}
        for item in ratios:
            name = item.select_one("span.name")
            value = item.select_one("span.number")
            if name and value:
                key = name.text.strip()
                val = value.text.strip()
                key_metrics[key] = val
        data["key_metrics"] = key_metrics

        # 2. TABLE PARSER
        def parse_table(section_id):
            section = soup.find("section", {"id": section_id})
            if not section:
                return None
            table = section.find("table")
            if not table:
                return None
            
            headers = [th.text.strip() for th in table.find_all("th")]
            rows = []
            for tr in table.find_all("tr")[1:]:
                cols = [td.text.strip() for td in tr.find_all(["td", "th"])]
                if len(cols) == len(headers):
                    rows.append(cols)
            
            # Convert to list of dicts for LLM readability
            if rows:
                df = pd.DataFrame(rows, columns=headers)
                return df.to_dict(orient='records')
            return None

        # 3. FINANCIAL TABLES
        data["quarterly"] = parse_table("quarters")
        data["profit_loss"] = parse_table("profit-loss")
        data["balance_sheet"] = parse_table("balance-sheet")
        data["cash_flow"] = parse_table("cash-flow")

        return data
    except Exception as e:
        logger.error(f"Error scraping screener data for {symbol}: {e}")
        return {"error": f"Failed to fetch data for {symbol}: {str(e)}"}

# ── Parallel-execution verification callback ─────────────────────────────────
def _fundamental_before_callback(callback_context: CallbackContext) -> Optional[object]:
    """Logs start time + thread ID so we can verify parallel execution.

    Compare with the news_agent log line:
      - Same time + same thread  → sequential (bad)
      - Same time + diff thread  → true parallel (good)
    """
    now = datetime.now()
    thread_id = threading.get_ident()
    logger.info(
        f"┌ [PARALLEL CHECK] fundamental_analysis_agent STARTED"
        f" | time={now.strftime('%H:%M:%S.%f')[:-3]}"
        f" | thread_id={thread_id}"
    )
    return None  # None = let the agent run normally


# Create Fundamental LlmAgent
fundamental_llm_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='fundamental_analysis_agent',
    description='Analyzes company fundamentals and financial health',
    # output_key tells ADK to automatically save this agent's final response
    # into session.state["fundamental_result"] so other agents can read it.
    output_key='fundamental_result',
    instruction="""You are a fundamental analysis expert for Indian stock markets.
    
    Your responsibilities:
    1. Analyze key financial metrics (P/E, P/B, ROE, debt ratios, etc.)
    2. Evaluate sales growth and profit trends
    3. Assess company's future plans and strategic initiatives
    4. Compare fundamentals across companies and sectors
    5. Identify value opportunities and red flags
    
    Use the available tools to fetch financial data and analyze fundamentals.
    Provide comprehensive analysis with proper valuation context.
    Always consider both quantitative metrics and qualitative factors.
    """,
    tools=[get_financial_metrics, analyze_growth_trends, evaluate_company_plans, get_screener_data],
)

logger.info("Fundamental Analysis Agent initialized")
