from typing import List

def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    Calculates the Relative Strength Index (RSI) using pure Python.
    
    Formula:
    RSI = 100 - (100 / (1 + RS))
    Where RS = Average Gain / Average Loss
    
    Args:
        prices: List of closing prices (must have at least 'period' + 1 elements).
        period: The lookback window (standard is 14).
        
    Returns:
        float: The current RSI value (0-100).
    """
    if len(prices) < period + 1:
        raise ValueError(f"Not enough data to calculate RSI. Need at least {period + 1} prices.")

    # 1. Calculate price changes
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    # 2. Calculate initial Average Gain/Loss (Simple Average)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # 3. Calculate Smoothed Averages (Wilder's Smoothing Method)
    # This is the industry standard used by trading platforms, not just simple average.
    for i in range(period, len(prices) - 1):
        current_gain = gains[i]
        current_loss = losses[i]
        
        avg_gain = ((avg_gain * (period - 1)) + current_gain) / period
        avg_loss = ((avg_loss * (period - 1)) + current_loss) / period

    # 4. Calculate RS and RSI
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)