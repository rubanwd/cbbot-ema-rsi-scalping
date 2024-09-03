
# risk_management.py

class RiskManagement:
    def __init__(self, atr_period=14, atr_multiplier=1.5, risk_ratio=1.5):
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.risk_ratio = risk_ratio

    def calculate_atr(self, df):
        high = df['high'].astype(float)
        low = df['low'].astype(float)
        close = df['close'].astype(float)

        df['previous_close'] = close.shift(1)
        df['tr1'] = high - low
        df['tr2'] = abs(high - df['previous_close'])
        df['tr3'] = abs(low - df['previous_close'])
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        atr = df['tr'].rolling(window=self.atr_period).mean().iloc[-1]
        return atr

    def calculate_risk_management(self, current_price, trend, df):
        atr = self.calculate_atr(df)
        
        stop_loss_distance = self.atr_multiplier * atr
        
        if trend == 'long':
            stop_loss = float(current_price) - stop_loss_distance
            take_profit = float(current_price) + (stop_loss_distance * self.risk_ratio)
        elif trend == 'short':
            stop_loss = float(current_price) + stop_loss_distance
            take_profit = float(current_price) - (stop_loss_distance * self.risk_ratio)
        else:
            raise ValueError("Trend must be either 'long' or 'short'")
        
        return stop_loss, take_profit
