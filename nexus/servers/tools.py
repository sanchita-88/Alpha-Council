import yfinance as yf
from duckduckgo_search import DDGS # The 'ddgs' package still uses this import
from nexus.servers.registry import registry
from nexus.indicators.rsi import calculate_rsi
from nexus.indicators.sma import calculate_sma

# --- HELPER FUNCTIONS ---

def fetch_price_history(ticker: str, period: str = "3mo") -> list[float]:
    """Fetches historical closing prices."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty: return []
        return df['Close'].tolist()
    except Exception as e:
        print(f"Connection Error: {e}")
        return []

# --- AGENT TOOLS ---

@registry.register("get_technical_summary")
def get_technical_summary(ticker: str) -> dict:
    """[Technical Agent] Returns deterministic indicators (RSI, SMA)."""
    prices = fetch_price_history(ticker)
    
    if not prices or len(prices) < 50:
        return {"error": f"Not enough data for {ticker}", "status": "failed"}

    current_price = round(prices[-1], 2)
    rsi = calculate_rsi(prices, period=14)
    sma_50 = calculate_sma(prices, period=50)

    signal = "HOLD"
    if rsi < 30: signal = "BUY (Oversold)"
    elif rsi > 70: signal = "SELL (Overbought)"

    return {
        "ticker": ticker.upper(),
        "current_price": current_price,
        "indicators": {
            "rsi_14": rsi,
            "sma_50": sma_50,
            "signal": signal
        },
        "data_source": "yfinance_live"
    }

@registry.register("get_market_news")
def get_market_news(query: str) -> list[dict]:
    """[Risk Agent] Searches DuckDuckGo for news."""
    try:
        # We use max_results=3 to keep it fast
        results = DDGS().text(keywords=f"{query} stock news", region='us-en', max_results=3)
        if not results:
            return [{"error": "No news found."}]
            
        clean_results = []
        for r in results:
            clean_results.append({
                "title": r.get('title'),
                "url": r.get('href'),
                "snippet": r.get('body')
            })
        return clean_results
    except Exception as e:
        return [{"error": f"Search failed: {str(e)}"}]

@registry.register("get_company_info")
def get_company_info(ticker: str) -> dict:
    """[Fundamental Agent] Fetches comprehensive financial health data."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # KEY UPDATE: Added Debt, Margins, and Growth for the Fundamental Agent
        return {
            "ticker": ticker.upper(),
            "name": info.get('longName', 'Unknown'),
            "sector": info.get('sector', 'Unknown'),
            "market_cap": info.get('marketCap', 'N/A'),
            "pe_ratio": info.get('trailingPE', 'N/A'),
            "forward_pe": info.get('forwardPE', 'N/A'),
            "dividend_yield": info.get('dividendYield', 'N/A'),
            # New Metrics added below:
            "profit_margins": info.get('profitMargins', 'N/A'),
            "revenue_growth": info.get('revenueGrowth', 'N/A'),
            "debt_to_equity": info.get('debtToEquity', 'N/A'),
            "free_cashflow": info.get('freeCashflow', 'N/A'),
            "data_source": "yfinance_fundamentals"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}