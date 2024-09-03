# indicators.py

import pandas as pd

class Indicators:
    @staticmethod
    def calculate_ema(df, span):
        """Calculate Exponential Moving Average (EMA)."""
        return df['close'].ewm(span=span, adjust=False).mean()

    @staticmethod
    def calculate_rsi(df, period=14):
        """Calculate Relative Strength Index (RSI)."""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
