import pandas as pd
from indicators import Indicators

class Strategies:
    def __init__(self):
        self.indicators = Indicators()

    def prepare_dataframe(self, historical_data):
        df = pd.DataFrame(historical_data)
        df.columns = ["timestamp", "open", "high", "low", "close", "volume", "turnover"]
        df['close'] = df['close'].astype(float)
        df.sort_values('timestamp', inplace=True)
        return df

    def scalping_strategy(self, df):
        ema_15 = df['EMA_15'].iloc[-1]
        rsi = df['RSI'].iloc[-1]

        if ema_15 > df['close'].iloc[-1] and rsi < 30:  # Oversold and below EMA
            return 'long'
        elif ema_15 < df['close'].iloc[-1] and rsi > 70:  # Overbought and above EMA
            return 'short'
        return None
