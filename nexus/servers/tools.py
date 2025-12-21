import yfinance as yf
from nexus.servers.registry import registry
from nexus.indicators.rsi import calculate_rsi
from nexus.indicators.sma import calculate_sma

def fetch_price_history(ticker: str, period: str = "3mo") -> list[float]:
    """
    Fetches historical closing prices from Yahoo Finance.
    Returns a list of floats.
    """
    try:
        # 1. Download data (quietly)
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        
        if df.empty:
            print(f"Error: No data found for {ticker}")
            return []
            
        # 2. Convert to simple list of floats
        return df['Close'].tolist()
        
    except Exception as e:
        print(f"Connection Error: {e}")
        return []

@registry.register("get_technical_summary")
def get_technical_summary(ticker: str) -> dict:
    """
    Returns deterministic technical indicators for a ticker using LIVE DATA.
    """
    # 1. Fetch Real Data
    prices = fetch_price_history(ticker)
    
    if not prices or len(prices) < 50:
        return {"error": f"Not enough data for {ticker}", "status": "failed"}

    current_price = round(prices[-1], 2)

    # 2. Compute Deterministic Indicators
    rsi = calculate_rsi(prices, period=14)
    sma_50 = calculate_sma(prices, period=50)

    # 3. Generate Signal
    signal = "HOLD"
    if rsi < 30: signal = "BUY (Oversold)"
    elif rsi > 70: signal = "SELL (Overbought)"

    # 4. Return Pure JSON
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