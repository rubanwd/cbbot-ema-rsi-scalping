import pandas as pd
import time

class RiskManagement:
    def __init__(self, atr_period=14, atr_multiplier=1.5, risk_ratio=1.5, position_timeout=300, data_fetcher=None):
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.risk_ratio = risk_ratio
        self.position_timeout = position_timeout  # In seconds (default: 5 minutes)
        self.data_fetcher = data_fetcher  # Store the data_fetcher object

    def calculate_atr(self, df):
        high = df['high'].astype(float)
        low = df['low'].astype(float)
        close = df['close'].astype(float)
        df['previous_close'] = close.shift(1)
        df['tr'] = pd.concat([high - low, (high - df['previous_close']).abs(), (low - df['previous_close']).abs()], axis=1).max(axis=1)
        atr = df['tr'].rolling(window=self.atr_period).mean().iloc[-1]
        return atr

    def calculate_dynamic_risk_management(self, df, current_price, trend):
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

    def monitor_position_timeout(self, order_result, symbol):
        """
        Monitors the position and closes it if the timeout has been reached.
        :param order_result: The result of the order placement.
        :param symbol: The symbol for the trade (e.g., 'BTCUSDT').
        """
        order_id = order_result.get('orderId')

        if not order_id:
            print("No valid order ID found, skipping timeout monitoring.")
            return

        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > self.position_timeout:
                print(f"Position open for more than {self.position_timeout // 60} minutes, closing it.")
                self.data_fetcher.cancel_order(order_id, symbol)  # Use the data_fetcher object to cancel the order
                break
            time.sleep(10)  # Check every 10 seconds
