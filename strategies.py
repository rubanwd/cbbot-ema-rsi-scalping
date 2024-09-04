# strategy.py

import pandas as pd
from indicators import Indicators

class Strategies:
    def __init__(self):
        self.indicators = Indicators()

    def prepare_dataframe(self, historical_data):
        """Convert response to DataFrame and sort it by timestamp."""
        df = pd.DataFrame(historical_data)
        df.columns = ["timestamp", "open", "high", "low", "close", "volume", "turnover"]
        df['close'] = df['close'].astype(float)
        
        # Sort by timestamp in ascending order
        df.sort_values('timestamp', inplace=True)

        return df

    def ema_rsi_strategy(self, historical_data):
        # Prepare the DataFrame
        df = self.prepare_dataframe(historical_data)
        
        # Calculate EMA 9 and EMA 21
        df['EMA_9'] = self.indicators.calculate_ema(df, 9)
        df['EMA_21'] = self.indicators.calculate_ema(df, 21)

        # Calculate RSI (14-period)
        df['RSI'] = self.indicators.calculate_rsi(df, 14)

        # Get the latest values
        ema_9 = df['EMA_9'].iloc[-1]
        ema_21 = df['EMA_21'].iloc[-1]
        rsi = df['RSI'].iloc[-1]

        print(f"EMA 9: {ema_9:.2f}")
        print(f"EMA 21: {ema_21:.2f}")
        print(f"RSI: {rsi:.2f}")

        if ema_9 > ema_21 and rsi > 50:
            return 'short'
        elif ema_9 < ema_21 and rsi < 50:
            return 'long'
        else:
            return None