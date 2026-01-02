import yfinance as yf
import json
from ddgs import DDGS

# Proper Modular Imports (These will work after Phase 4)
from nexus.indicators.sma import calculate_sma, is_uptrend
from nexus.indicators.rsi import calculate_rsi

def get_technical_summary(ticker: str) -> str:
    """Fetches data and calculates technical indicators."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        
        if hist.empty:
            return "Error: No data found for ticker."

        # Extract Series
        closes = hist['Close']
        
        # Calculate Indicators using your modular functions
        current_price = closes.iloc[-1]
        rsi = calculate_rsi(closes)
        sma_50 = calculate_sma(closes, 50)
        sma_20 = calculate_sma(closes, 20)
        trend = is_uptrend(current_price, sma_50)

        data = {
            "ticker": ticker,
            "price": round(current_price, 2),
            "rsi": rsi,
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "is_uptrend": bool(trend),
            "volume": int(hist['Volume'].iloc[-1])
        }
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error in technical analysis: {e}"

def get_company_info(ticker: str) -> str:
    """Fetches fundamental data."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        data = {
            "ticker": ticker,
            "sector": info.get('sector', 'Unknown'),
            "pe_ratio": info.get('trailingPE', 0),
            "margins": info.get('profitMargins', 0),
            "debt_equity": info.get('debtToEquity', 0)
        }
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error fetching fundamentals: {e}"

def get_market_news(query: str) -> str:
    """Searches for news."""
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No news found."
        
        formatted = [f"- {r['title']} ({r['href']})" for r in results]
        return "\n".join(formatted)
    except Exception as e:
        return f"Error searching news: {e}"