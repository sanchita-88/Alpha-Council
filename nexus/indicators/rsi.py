import pandas as pd

def calculate_rsi(series: pd.Series, period: int = 14) -> float:
    """Calculates the Relative Strength Index (RSI)."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs.iloc[-1]))
    return round(rsi, 2)