import yfinance as yf
from duckduckgo_search import DDGS
from mcp.server.fastmcp import FastMCP
import logging
import os

# 1. Silence all background noise
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
os.environ['YF_NO_PRINTOUT'] = '1'

mcp = FastMCP("AlphaCouncil Finance")

@mcp.tool()
def analyze_stock(ticker: str) -> str:
    """Fetches stock price and trend."""
    try:
        stock = yf.Ticker(ticker)
        # .history does NOT accept progress=False in current versions
        hist = stock.history(period="1mo")
        
        if hist.empty:
            return f"Error: No data found for ticker {ticker}"
            
        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
        latest = hist.iloc[-1]
        trend = "Bullish" if latest['Close'] > latest['SMA_20'] else "Bearish"
        
        return (
            f"Price: ${latest['Close']:.2f}\n"
            f"Trend: {trend}\n"
            f"Volume: {latest['Volume']}\n"
            f"Note: {'Above' if trend == 'Bullish' else 'Below'} SMA 20"
        )
    except Exception as e:
        return f"Tech Tool Error: {str(e)}"

@mcp.tool()
def get_fundamentals(ticker: str) -> str:
    """Fetches valuation and margin data."""
    try:
        stock = yf.Ticker(ticker)
        # info can be slow or chatty; we use it carefully
        info = stock.info
        
        return (
            f"Market Cap: {info.get('marketCap', 'N/A')}\n"
            f"P/E Ratio: {info.get('trailingPE', 'N/A')}\n"
            f"Sector: {info.get('sector', 'N/A')}\n"
            f"Margins: {info.get('profitMargins', 'N/A')}"
        )
    except Exception as e:
        return f"Fund Tool Error: {str(e)}"

import time
import random

@mcp.tool()
def search_news(query: str) -> str:
    try:
        # 1. Add a tiny random sleep to dodge bot detection (0.5 to 1.5 seconds)
        time.sleep(random.uniform(0.5, 1.5))
        
        # 2. Use a more specific query to force fresh results
        fresh_query = f"{query} stock news Jan 2026" 
        
        with DDGS() as ddgs:
            # max_results=5 gives the LLM more 'meat' to work with
            results = list(ddgs.text(fresh_query, max_results=5))
            
        if not results:
            return "No recent news found. Market may be quiet or search blocked."
        
        return "\n".join([f"- {r['title']} ({r['href']})" for r in results])
    except Exception as e:
        # If DDG blocks us, let's at least know why
        if "202" in str(e) or "Ratelimit" in str(e):
            return "ERROR: News search is currently rate-limited by DuckDuckGo."
        return f"News Tool Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()