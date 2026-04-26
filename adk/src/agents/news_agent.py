"""News Intelligence Agent - Analyzes news and sentiment for stocks/indices."""
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from typing import Dict, Any, List, Optional
import feedparser
import httpx
from datetime import datetime
from loguru import logger
from ..tools.backend_client import get_backend_client
from ..cache import get_cache_client


async def fetch_rss_news(symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch news from RSS feeds for a stock symbol.
    
    Args:
        symbol: Stock symbol
        limit: Number of news articles to retrieve
        
    Returns:
        List of news articles with title, link, published date, and summary
    """
    try:
        # Google News RSS feed for the stock
        rss_url = f"https://news.google.com/rss/search?q={symbol}+stock+india&hl=en-IN&gl=IN&ceid=IN:en"
        
        logger.info(f"Fetching RSS news from: {rss_url}")
        
        # Fetch RSS feed
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(rss_url)
            response.raise_for_status()
            
        # Parse RSS feed
        feed = feedparser.parse(response.text)
        
        news_articles = []
        for entry in feed.entries[:limit]:
            article = {
                "title": entry.get("title", "No title"),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", "No summary available"),
                "source": entry.get("source", {}).get("title", "Unknown source")
            }
            news_articles.append(article)
        
        logger.info(f"Fetched {len(news_articles)} news articles for {symbol}")
        return news_articles
        
    except Exception as e:
        logger.error(f"Error fetching RSS news for {symbol}: {e}")
        return []


def get_stock_news(symbol: str, limit: int = 10) -> Dict[str, Any]:
    """Retrieves latest news for a stock symbol from RSS feeds.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'HDFCBANK', 'TCS')
        limit: Number of news articles to retrieve
        
    Returns:
        Dict containing news articles and metadata
    """
    try:
        # Try cache first (optional - skip if Redis not available)
        try:
            cache = get_cache_client()
            cached_news = cache.get_news(symbol, limit)
            if cached_news:
                logger.info(f"News for {symbol} found in cache")
                return {
                    "symbol": symbol,
                    "news": cached_news,
                    "source": "cache",
                    "count": len(cached_news)
                }
        except Exception as cache_error:
            logger.debug(f"Cache unavailable (Redis not running): {cache_error}")
        
        # Fetch from RSS feeds (synchronous wrapper for async function)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If event loop is running, create a new one in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, fetch_rss_news(symbol, limit))
                    news_articles = future.result()
            else:
                news_articles = asyncio.run(fetch_rss_news(symbol, limit))
        except Exception as e:
            logger.warning(f"Error with async execution: {e}, falling back to sync")
            news_articles = []
        
        if news_articles:
            return {
                "symbol": symbol,
                "news": news_articles,
                "source": "rss_feed",
                "count": len(news_articles),
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "symbol": symbol,
            "news": [],
            "source": "rss_feed",
            "count": 0,
            "message": "No news articles found"
        }
        
    except Exception as e:
        logger.error(f"Error fetching news for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e)}


def analyze_sentiment(symbol: str) -> Dict[str, Any]:
    """Analyzes overall sentiment for a stock from recent news.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Sentiment analysis including score and key factors
    """
    try:
        cache = get_cache_client()
        
        # Try cache first
        cached_sentiment = cache.get_sentiment(symbol)
        if cached_sentiment:
            logger.info(f"Sentiment for {symbol} found in cache")
            return cached_sentiment
        
        # Placeholder for backend call
        return {
            "symbol": symbol,
            "sentiment_score": 0.0,
            "sentiment_label": "neutral",
            "message": "Backend integration pending"
        }
    except Exception as e:
        logger.error(f"Error analyzing sentiment for {symbol}: {e}")
        return {"error": str(e)}



# Create the News LlmAgent
news_llm_agent = LlmAgent(
    model='gemini-2.5-flash-lite',
    name='news_intelligence_agent',
    description='Analyzes news and sentiment for stocks and indices using RSS feeds',
    # output_key tells ADK to automatically save this agent's final response
    # into session.state["news_result"] so other agents can read it.
    output_key='news_result',
    instruction="""You are a financial news analysis expert specializing in Indian stock markets.
    
    Your responsibilities:
    1. Fetch and analyze latest news for stocks and indices from RSS feeds
    2. Provide sentiment analysis (positive, negative, neutral)
    3. Identify market-moving events and their potential impact
    4. Extract key insights from news articles
    5. Correlate news with stock/index performance
    
    Use the available tools to fetch news and analyze sentiment.
    Always provide data-driven insights with proper context.
    Highlight both opportunities and risks mentioned in the news.
    
    When fetching news, use the stock symbol (e.g., 'RELIANCE', 'TCS', 'HDFCBANK').
    The news comes from Google News RSS feeds with real-time updates.
    """,
    tools=[get_stock_news],
)

logger.info("News Intelligence Agent initialized with RSS feed support")
