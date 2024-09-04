# strategy.py

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

    def combine_indicators_strategy(self, df):
        ema_9 = df['EMA_9'].iloc[-1]
        ema_21 = df['EMA_21'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        macd = df['MACD'].iloc[-1]
        macd_signal = df['MACD_signal'].iloc[-1]
        stochastic = df['Stochastic'].iloc[-1]
        stochastic_signal = df['Stochastic_signal'].iloc[-1]

        if ema_9 > ema_21 and rsi > 50 and macd > macd_signal and stochastic > stochastic_signal:
            return 'long'
        elif ema_9 < ema_21 and rsi < 50 and macd < macd_signal and stochastic < stochastic_signal:
            return 'short'
        return None
