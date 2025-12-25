import pandas as pd

def calculate_sma(series: pd.Series, window: int) -> float:
    """Calculates the Simple Moving Average."""
    if len(series) < window:
        return 0.0
    return series.rolling(window=window).mean().iloc[-1]

def is_uptrend(price: float, sma_50: float) -> bool:
    """Returns True if Price > SMA 50."""
    return price > sma_50