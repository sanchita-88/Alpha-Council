import unittest
import sys
import os

# Add the parent directory to the path so we can import 'indicators'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from indicators.rsi import calculate_rsi

class TestIndicators(unittest.TestCase):
    
    def test_rsi_constant_uptrend(self):
        """Test RSI on a perfect uptrend (Should be 100)."""
        # Prices go up by 1 every day: 1, 2, 3... 20
        prices = [float(i) for i in range(1, 21)]
        # RSI should be very high (near 100)
        rsi = calculate_rsi(prices, period=14)
        print(f"DEBUG: Constant Uptrend RSI = {rsi}")
        self.assertTrue(rsi > 90, "RSI should be > 90 for constant uptrend")

    def test_rsi_constant_downtrend(self):
        """Test RSI on a perfect downtrend (Should be 0)."""
        # Prices go down by 1 every day: 20, 19, 18... 1
        prices = [float(i) for i in range(20, 0, -1)]
        rsi = calculate_rsi(prices, period=14)
        print(f"DEBUG: Constant Downtrend RSI = {rsi}")
        self.assertTrue(rsi < 10, "RSI should be < 10 for constant downtrend")

    def test_rsi_flat_prices(self):
        """Test RSI on flat prices (Should be ~50 or undefined behavior handled)."""
        # Prices stay at 100
        prices = [100.0] * 20
        # If no gains and no losses, standard definition varies, 
        # but our function handles div/0 by returning 100 or 50 depending on implementation.
        # Let's see what yours returns.
        rsi = calculate_rsi(prices, period=14)
        print(f"DEBUG: Flat Price RSI = {rsi}")
        # Usually implies stability
        self.assertIsNotNone(rsi)

if __name__ == '__main__':
    unittest.main()