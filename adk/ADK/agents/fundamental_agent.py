"""Fundamental Analysis Agent - Evaluates financial metrics and company fundamentals."""

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from loguru import logger
import requests
from bs4 import BeautifulSoup
import pandas as pd
from ..cache import get_cache_client

# TTL for screener data: 1 hour (financial statements don't change intraday)
_SCREENER_TTL = 3600

# Normalizes common index aliases to screener.in URL slugs
_SYMBOL_SLUG_MAP = {
    "NIFTY50": "NIFTY",
    "NIFTY": "NIFTY",
    "BANKNIFTY": "BANKNIFTY",
    "NIFTYBANK": "BANKNIFTY",
}


def get_screener_data(symbol: str) -> Dict[str, Any]:
    """Scrapes comprehensive data for an Indian stock or index from Screener.in.

    Results are cached in Redis for 1 hour so repeated queries for the same
    symbol skip the scrape entirely.

    Includes key ratios, quarterly results, profit & loss statements,
    balance sheets, and cash flow data.

    Args:
        symbol: Stock symbol or index name (e.g., 'TCS', 'RELIANCE', 'NIFTY50', 'BANKNIFTY')

    Returns:
        Dict containing key metrics and financial tables
    """
    # Resolve index aliases to their screener slugs
    slug = _SYMBOL_SLUG_MAP.get(symbol.upper(), symbol.upper())

    # --- cache read ---
    try:
        cache = get_cache_client()
        cached = cache.get(f"screener:{slug}")
        if cached:
            logger.info(f"Screener data for {slug} served from cache")
            return cached
    except Exception as e:
        logger.warning(f"Cache read failed, falling back to scrape: {e}")

    # --- scrape ---
    try:
        url = f"https://www.screener.in/company/{slug}/"
        headers = {"User-Agent": "Mozilla/5.0"}

        logger.info(f"Scraping screener data for {slug}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        data = {}

        # Top ratios (key metrics)
        ratios = soup.select("ul#top-ratios li")
        key_metrics = {}
        for item in ratios:
            name = item.select_one("span.name")
            value = item.select_one("span.number")
            if name and value:
                key_metrics[name.text.strip()] = value.text.strip()
        data["key_metrics"] = key_metrics

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
            if rows:
                return pd.DataFrame(rows, columns=headers).to_dict(orient="records")
            return None

        data["quarterly"] = parse_table("quarters")
        data["profit_loss"] = parse_table("profit-loss")
        data["balance_sheet"] = parse_table("balance-sheet")
        data["cash_flow"] = parse_table("cash-flow")
        data["shareholding"] = parse_table("shareholding")

        # Also fetch last 1 month of daily price history from Yahoo Finance
        data["history_1mo"] = get_historical_data(symbol, range="1mo", interval="1d")

        # --- cache write ---
        try:
            cache.set(f"screener:{slug}", data, ttl=_SCREENER_TTL)
            logger.info(f"Screener data for {slug} cached for {_SCREENER_TTL}s")
        except Exception as e:
            logger.warning(f"Cache write failed (data still returned): {e}")

        return data

    except Exception as e:
        logger.error(f"Error scraping screener data for {slug}: {e}")
        return {"error": f"Failed to fetch data for {symbol}: {str(e)}"}


# Yahoo Finance suffix map for NSE indices and stocks
_YAHOO_SUFFIX_MAP = {
    "NIFTY50": "^NSEI",
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "NIFTYBANK": "^NSEBANK",
}

# TTL for price history: 6 hours (intraday changes but daily OHLCV is stable)
_HISTORY_TTL = 21600

_VALID_RANGES = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}
_VALID_INTERVALS = {"1d", "1wk", "1mo"}


def get_historical_data(symbol: str, range: str = "1y", interval: str = "1d") -> Dict[str, Any]:
    """Fetches and returns clean OHLCV price history for a stock or index from Yahoo Finance.

    Args:
        symbol:   NSE stock symbol or index alias
                  (e.g. 'TCS', 'RELIANCE', 'NIFTY50', 'BANKNIFTY')
        range:    Time range — '1d','5d','1mo','3mo','6mo','1y','2y','5y','10y','ytd','max'
                  Defaults to '1y'.
        interval: Bar size — '1d' (daily), '1wk' (weekly), '1mo' (monthly).
                  Defaults to '1d'.

    Returns:
        Dict with keys:
          - symbol        : resolved Yahoo ticker
          - range / interval
          - currency
          - current_price : latest closing price
          - 52w_high / 52w_low
          - bars          : list of {date, open, high, low, close, adj_close, volume}
          - summary       : human-readable price trend summary
    """
    if range not in _VALID_RANGES:
        return {"error": f"Invalid range '{range}'. Valid: {sorted(_VALID_RANGES)}"}
    if interval not in _VALID_INTERVALS:
        return {"error": f"Invalid interval '{interval}'. Valid: {sorted(_VALID_INTERVALS)}"}

    # Resolve symbol to Yahoo ticker
    upper = symbol.upper()
    if upper in _YAHOO_SUFFIX_MAP:
        ticker = _YAHOO_SUFFIX_MAP[upper]
    else:
        ticker = f"{upper}.NS"

    cache_key = f"yahoo:{ticker}:{range}:{interval}"
    try:
        cache = get_cache_client()
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Historical data for {ticker} served from cache")
            return cached
    except Exception as e:
        logger.warning(f"Cache read failed: {e}")

    try:
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            f"?range={range}&interval={interval}"
        )
        headers = {"User-Agent": "Mozilla/5.0"}
        logger.info(
            f"Fetching Yahoo Finance history for {ticker} range={range} interval={interval}"
        )
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        raw = response.json()

        result = raw.get("chart", {}).get("result")
        if not result:
            err = raw.get("chart", {}).get("error") or "No data returned"
            return {"error": str(err)}

        result = result[0]
        meta = result.get("meta", {})
        timestamps: List[int] = result.get("timestamp", [])
        quote = result.get("indicators", {}).get("quote", [{}])[0]
        adjclose_list: List[Optional[float]] = (
            result.get("indicators", {}).get("adjclose", [{}])[0].get("adjclose", [])
        )

        # Build clean bar list — skip bars where close is None (market holiday gaps)
        bars: List[Dict[str, Any]] = []
        for i, ts in enumerate(timestamps):
            close = quote.get("close", [])[i] if i < len(quote.get("close", [])) else None
            if close is None:
                continue
            bars.append(
                {
                    "date": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d"),
                    "open": (
                        round(quote.get("open", [])[i], 2)
                        if i < len(quote.get("open", [])) and quote.get("open", [])[i]
                        else None
                    ),
                    "high": (
                        round(quote.get("high", [])[i], 2)
                        if i < len(quote.get("high", [])) and quote.get("high", [])[i]
                        else None
                    ),
                    "low": (
                        round(quote.get("low", [])[i], 2)
                        if i < len(quote.get("low", [])) and quote.get("low", [])[i]
                        else None
                    ),
                    "close": round(close, 2),
                    "adj_close": (
                        round(adjclose_list[i], 2)
                        if i < len(adjclose_list) and adjclose_list[i]
                        else None
                    ),
                    "volume": (
                        quote.get("volume", [])[i] if i < len(quote.get("volume", [])) else None
                    ),
                }
            )

        # Summary stats
        closes = [b["close"] for b in bars if b["close"] is not None]
        first_close = closes[0] if closes else None
        last_close = closes[-1] if closes else None
        pct_change = (
            round((last_close - first_close) / first_close * 100, 2) if first_close else None
        )

        data: Dict[str, Any] = {
            "symbol": ticker,
            "range": range,
            "interval": interval,
            "currency": meta.get("currency"),
            "current_price": meta.get("regularMarketPrice"),
            "52w_high": meta.get("fiftyTwoWeekHigh"),
            "52w_low": meta.get("fiftyTwoWeekLow"),
            "bar_count": len(bars),
            "bars": bars,
            "summary": {
                "first_date": bars[0]["date"] if bars else None,
                "last_date": bars[-1]["date"] if bars else None,
                "first_close": first_close,
                "last_close": last_close,
                "pct_change": pct_change,
                "trend": (
                    "up"
                    if pct_change and pct_change > 0
                    else "down" if pct_change and pct_change < 0 else "flat"
                ),
            },
        }

        print(f"\n=== {data['symbol']} SUMMARY ===")
        print(f"Range: {data['range']} | Interval: {data['interval']}")
        print(f"Currency: {data['currency']}")
        print(f"Current Price: {data['current_price']}")
        print(f"52W High: {data['52w_high']}")
        print(f"52W Low: {data['52w_low']}")
        print(f"Bars: {data['bar_count']}")
        print(f"Trend: {data['summary']['trend']}")
        print(f"Change: {data['summary']['pct_change']}%\n")

        print("=== BARS ===")
        for bar in data["bars"]:
            print(bar)

        try:
            cache = get_cache_client()
            cache.set(cache_key, data, ttl=_HISTORY_TTL)
            logger.info(f"Historical data for {ticker} cached for {_HISTORY_TTL}s")
        except Exception as e:
            logger.warning(f"Cache write failed (data still returned): {e}")

        return data

    except Exception as e:
        logger.error(f"Error fetching Yahoo Finance data for {ticker}: {e}")
        return {"error": f"Failed to fetch historical data for {symbol}: {str(e)}"}


# def _fundamental_after_agent_callback(callback_context: CallbackContext):
#     """Log confirmation that output_key has written fundamental_result to session state."""
#     fundamental_result = callback_context.state.get("fundamental_result")
#     if fundamental_result:
#         logger.info(
#             f"[fundamental_after_agent_callback] fundamental_result in state ({len(str(fundamental_result))} chars)"
#         )
#     else:
#         logger.warning(
#             "[fundamental_after_agent_callback] fundamental_result not found in state after agent run"
#         )
#     return None


def make_fundamental_agent() -> LlmAgent:
    """Factory — returns a fresh LlmAgent instance each call to avoid ADK re-parenting errors."""
    return LlmAgent(
        model="gemini-2.5-flash",
        name="fundamental_analysis_agent",
        description="Analyzes company fundamentals and financial health",
        output_key="fundamental_result",
        instruction="""You are a fundamental analysis expert for Indian stock markets and indices.

    When asked to analyze a stock or index, call get_screener_data(symbol) to retrieve all
    available financial data in one call.

    Supported symbols:
    - Stocks: NSE symbol directly (e.g., 'TCS', 'RELIANCE', 'HDFCBANK')
    - Indices: 'NIFTY50' or 'NIFTY' for Nifty 50, 'BANKNIFTY' or 'NIFTYBANK' for Bank Nifty

    The tool returns:
      - key_metrics   : valuation ratios (P/E, P/B, ROE, EPS, market cap, dividend yield, etc.)
      - quarterly      : recent quarterly revenue, profit, and margin data
      - profit_loss    : multi-year P&L statement (sales, expenses, net profit, OPM)
      - balance_sheet  : assets, liabilities, equity, and debt breakdown
      - cash_flow      : operating, investing, and financing cash flows
      - shareholding   : promoter, FII, DII, and public holding patterns

    Available tools:
    - get_screener_data(symbol)       — fundamentals: ratios, P&L, balance sheet, cash flow, shareholding
    - get_historical_data(symbol, range, interval) — OHLCV price history from Yahoo Finance
        range options    : '1d','5d','1mo','3mo','6mo','1y','2y','5y','10y','ytd','max'
        interval options : '1d' (daily), '1wk' (weekly), '1mo' (monthly)

    Always call get_screener_data first for fundamental context. Call get_historical_data
    additionally when the user asks about price trends, momentum, entry points, or historical performance.

    For stocks, deliver a structured analysis covering:
    1. Valuation — is the stock cheap, fairly valued, or expensive vs. peers and history?
    2. Profitability & margins — OPM, NPM, ROE, ROCE trends over time.
    3. Growth — revenue and profit CAGR; acceleration or deceleration signals.
    4. Financial health — debt-to-equity, interest coverage, current ratio.
    5. Cash flow quality — whether reported profits are backed by real cash generation.
    6. Shareholding trends — promoter pledge/increase, institutional interest.
    7. Price trend (if historical data fetched) — % change over period, 52w high/low, trend direction.
    8. Red flags & strengths — call out anything that stands out positively or negatively.
    9. Overall verdict — a concise buy / hold / avoid recommendation with key reasons.

    For indices, focus on:
    1. Valuation — index P/E, P/B vs historical averages (cheap / fair / expensive).
    2. Earnings growth — aggregate EPS growth trend of constituents.
    3. Sector composition — which sectors dominate and how that affects the index.
    4. Concentration risk — top 5 stock weightage and dependency risk.
    5. Price trend (if historical data fetched) — % change over period, 52w high/low, trend direction.
    6. Overall verdict — is the index attractively valued for long-term entry?

    Be precise with numbers. Reference specific figures from the data rather than speaking in generalities.
    """,
        tools=[get_screener_data, get_historical_data],
    )

logger.info("Fundamental Analysis Agent factory ready")
