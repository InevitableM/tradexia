"""News Intelligence Agent - Analyzes news and sentiment for stocks/indices."""

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from typing import Dict, Any, List
import feedparser
import httpx
from datetime import datetime
from loguru import logger
from ..cache import get_cache_client


def _fetch_rss_news_by_query(query: str, limit: int) -> List[Dict[str, Any]]:
    """Fetch news from Google News RSS feed using a synchronous HTTP client."""
    try:
        rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
        logger.info(f"Fetching RSS news for query: {query}")
        with httpx.Client(timeout=10.0) as client:
            response = client.get(rss_url)
            response.raise_for_status()
        feed = feedparser.parse(response.text)
        articles = []
        for entry in feed.entries[:limit]:
            articles.append(
                {
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", "No summary available"),
                    "source": entry.get("source", {}).get("title", "Unknown source"),
                }
            )
        logger.info(f"Fetched {len(articles)} articles for query: {query}")
        return articles
    except Exception as e:
        logger.error(f"Error fetching RSS news for query '{query}': {e}")
        return []


_INDEX_QUERY_MAP = {
    "NIFTY50": "NIFTY 50 index india",
    "NIFTY": "NIFTY 50 index india",
    "BANKNIFTY": "Bank Nifty index india",
    "NIFTYBANK": "Bank Nifty index india",
}


def get_stock_news(symbol: str) -> Dict[str, Any]:
    """Retrieves the latest 10 news articles for a stock symbol or index from Google News RSS.

    Args:
        symbol: Stock symbol or index name (e.g., 'RELIANCE', 'TCS', 'NIFTY50', 'BANKNIFTY')

    Returns:
        Dict containing news articles and metadata
    """
    limit = 10
    try:
        try:
            cache = get_cache_client()
            cached_news = cache.get_news(symbol, limit)
            if cached_news:
                logger.info(f"News for {symbol} found in cache")
                return {
                    "symbol": symbol,
                    "news": cached_news,
                    "source": "cache",
                    "count": len(cached_news),
                }
        except Exception as cache_error:
            logger.debug(f"Cache unavailable: {cache_error}")

        # Use a friendlier search query for known indices
        search_term = _INDEX_QUERY_MAP.get(symbol.upper(), f"{symbol} stock india")
        articles = _fetch_rss_news_by_query(search_term, limit)
        if articles:
            try:
                cache.set(f"news:{symbol}:{limit}", articles, ttl=900)
                logger.info(f"News for {symbol} cached for 900s")
            except Exception as cache_error:
                logger.warning(f"Cache write failed: {cache_error}")
            return {
                "symbol": symbol,
                "news": articles,
                "source": "rss_feed",
                "count": len(articles),
                "timestamp": datetime.now().isoformat(),
            }
        return {
            "symbol": symbol,
            "news": [],
            "source": "rss_feed",
            "count": 0,
            "message": "No news articles found",
        }
    except Exception as e:
        logger.error(f"Error fetching news for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e)}


def _news_after_agent_callback(callback_context: CallbackContext):
    """Log confirmation that output_key has written news_result to session state."""
    news_result = callback_context.state.get("news_result")
    if news_result:
        logger.info(
            f"[news_after_agent_callback] news_result in state ({len(str(news_result))} chars)"
        )
    else:
        logger.warning("[news_after_agent_callback] news_result not found in state after agent run")
    return None


def make_news_agent() -> LlmAgent:
    """Factory — returns a fresh LlmAgent instance each call to avoid ADK re-parenting errors."""
    return LlmAgent(
        model="gemini-2.5-flash-lite",
        name="news_intelligence_agent",
        description="Analyzes news and sentiment for stocks and indices using RSS feeds",
        output_key="news_result",
        after_agent_callback=_news_after_agent_callback,
        instruction="""You are a financial news analysis expert specializing in Indian stock markets and indices.

    When asked about a stock or index, call get_stock_news(symbol) to fetch the latest articles.

    Supported symbols:
    - Stocks: use the NSE symbol directly (e.g., 'RELIANCE', 'TCS', 'HDFCBANK')
    - Indices: use 'NIFTY50' for Nifty 50, 'BANKNIFTY' for Bank Nifty

    From the returned articles deliver a structured analysis covering:
    1. Overall sentiment — positive, negative, or neutral, with a brief justification.
    2. Key themes — group articles by topic (earnings, macro, regulatory, management, index rebalancing, RBI policy, etc.).
    3. Market-moving events — highlight any news that could directly impact the stock or index.
    4. Risks surfaced — note any warnings, downgrades, or concerns mentioned.
    5. Opportunities surfaced — note any positive catalysts, upgrades, or strategic wins.
    6. Sentiment verdict — one-line summary of what the news collectively signals.

    Be specific — reference article titles and sources rather than speaking in generalities.
    """,
        tools=[get_stock_news],
    )

logger.info("News Intelligence Agent factory ready")
