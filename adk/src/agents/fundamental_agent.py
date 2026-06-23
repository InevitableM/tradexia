"""Fundamental Analysis Agent - Evaluates financial metrics and company fundamentals."""
from google.adk.agents import LlmAgent
from typing import Dict, Any
from loguru import logger
import requests
from bs4 import BeautifulSoup
import pandas as pd


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
        data["shareholding"]= parse_table("shareholding")
        print(f"Scraped data for {symbol}: {data['shareholding']}")

        return data
    except Exception as e:
        logger.error(f"Error scraping screener data for {symbol}: {e}")
        return {"error": f"Failed to fetch data for {symbol}: {str(e)}"}


# Create Fundamental LlmAgent
fundamental_llm_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='fundamental_analysis_agent',
    description='Analyzes company fundamentals and financial health',
    # output_key tells ADK to automatically save this agent's final response
    # into session.state["fundamental_result"] so other agents can read it.
    output_key='fundamental_result',
    instruction="""You are a fundamental analysis expert for Indian stock markets.

    When asked to analyze a stock, call get_screener_data(symbol) to retrieve all available
    financial data in one call. The tool returns:
      - key_metrics   : valuation ratios (P/E, P/B, ROE, EPS, market cap, dividend yield, etc.)
      - quarterly      : recent quarterly revenue, profit, and margin data
      - profit_loss    : multi-year P&L statement (sales, expenses, net profit, OPM)
      - balance_sheet  : assets, liabilities, equity, and debt breakdown
      - cash_flow      : operating, investing, and financing cash flows
      - shareholding   : promoter, FII, DII, and public holding patterns

    Using that data, deliver a structured analysis covering:
    1. Valuation — is the stock cheap, fairly valued, or expensive vs. peers and history?
    2. Profitability & margins — OPM, NPM, ROE, ROCE trends over time.
    3. Growth — revenue and profit CAGR; acceleration or deceleration signals.
    4. Financial health — debt-to-equity, interest coverage, current ratio.
    5. Cash flow quality — whether reported profits are backed by real cash generation.
    6. Shareholding trends — promoter pledge/increase, institutional interest.
    7. Red flags & strengths — call out anything that stands out positively or negatively.
    8. Overall verdict — a concise buy / hold / avoid recommendation with key reasons.

    Be precise with numbers. Reference specific figures from the data rather than speaking in generalities.
    """,
    tools=[get_screener_data],
)

logger.info("Fundamental Analysis Agent initialized")
