from typing import List, Optional

def calculate_sma(prices: List[float], period: int = 50) -> Optional[float]:
    """
    Calculates the Simple Moving Average (SMA) using pure Python.
    
    Args:
        prices: List of closing prices.
        period: The window size (standard is 50 or 200).
        
    Returns:
        float: The SMA value, or None if not enough data.
    """
    if len(prices) < period:
        return None
        
    # Get the last 'period' prices
    window = prices[-period:]
    
    # Calculate average
    sma = sum(window) / period
    
    return round(sma, 2)