import schedule
import time
import logging
from data_fetcher import DataFetcher
from indicators import Indicators
from strategies import Strategies
from risk_management import RiskManagement
from dotenv import load_dotenv
import os
import pandas as pd
from bybit_demo_session import BybitDemoSession

class TradingBot:
    def __init__(self):
        load_dotenv()

        self.api_key = os.getenv("BYBIT_API_KEY")
        self.api_secret = os.getenv("BYBIT_API_SECRET") 

        if not self.api_key or not self.api_secret:
            raise ValueError("API keys not found. Please set BYBIT_API_KEY and BYBIT_API_SECRET in your .env file.")

        self.data_fetcher = BybitDemoSession(self.api_key, self.api_secret)

        self.strategy = Strategies()
        self.indicators = Indicators()
        self.risk_management = RiskManagement(
            atr_multiplier=float(os.getenv("ATR_MULTIPLIER", 1.0)),
            risk_ratio=float(os.getenv("RISK_RATIO", 1.0)),
            position_timeout=5 * 60,  # Timeout for scalping positions (5 minutes)
            data_fetcher=self.data_fetcher  # Pass data_fetcher to RiskManagement
        )
        self.symbol = os.getenv("TRADING_SYMBOL", 'BTCUSDT')
        self.quantity = float(os.getenv("TRADE_QUANTITY", 0.03))
        self.open_order_time = None  # Track when an order is placed

        # Load trading parameters
        self.interval = os.getenv("TRADING_INTERVAL", '1')
        self.limit = int(os.getenv("TRADING_LIMIT", 100))
        self.leverage = int(os.getenv("LEVERAGE", 10))

        # Set up logging
        logging.basicConfig(filename='trading_bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def job(self):
        # Check if an open order has timed out
        if self.open_order_time:
            elapsed_time = time.time() - self.open_order_time
            if elapsed_time > self.risk_management.position_timeout:
                print(f"Position open for more than {self.risk_management.position_timeout // 60} minutes, closing it.")
                open_orders = self.data_fetcher.get_open_orders(self.symbol)
                for order in open_orders:
                    self.data_fetcher.cancel_order(order['orderId'], self.symbol)
                self.open_order_time = None  # Reset after closing the order
                return

        last_closed_position = self.data_fetcher.get_last_closed_position(self.symbol)
        if last_closed_position:
            last_closed_time = int(last_closed_position['updatedTime']) / 1000
            current_time = time.time()
            time_since_last_close = current_time - last_closed_time
            print(f"Time since last closed position: {int(time_since_last_close)} seconds")
            if time_since_last_close < 120:
                print("The last closed position was less than 3 minutes ago. A new order will not be placed.")
                return

        get_historical_data = self.data_fetcher.get_historical_data(self.symbol, self.interval, self.limit)
        if get_historical_data is None:
            print("Failed to retrieve historical data.")
            return

        df = self.strategy.prepare_dataframe(get_historical_data)

        # Calculate indicators
        df['EMA_15'] = self.indicators.calculate_ema(df, 15)  # Faster EMA for scalping
        df['RSI'] = self.indicators.calculate_rsi(df, 7)    # Shorter RSI period

        # Get the latest indicator values
        ema_15 = df['EMA_15'].iloc[-1]
        rsi = df['RSI'].iloc[-1]

        # Print the indicator values
        print(f"EMA 15: {ema_15:.2f}")
        print(f"RSI: {rsi:.2f}")

        open_positions = self.data_fetcher.get_open_positions(self.symbol)
        if open_positions:
            print("There is already an open position. A new order will not be placed.")
            return

        current_price = self.data_fetcher.get_real_time_price(self.symbol)
        if current_price is None:
            print("Failed to retrieve real-time price.")
            return

        print(f"Current Price: {current_price:.2f}")

        trend = self.strategy.scalping_strategy(df)
        if trend:
            stop_loss, take_profit = self.risk_management.calculate_dynamic_risk_management(df, current_price, trend)
            print(f"Trend: {trend.upper()}")
            print(f"Stop Loss: {stop_loss:.2f}")
            print(f"Take Profit: {take_profit:.2f}")

            side = 'Buy' if trend == 'long' else 'Sell'
            print(f"Order side: {side}")

            order_result = self.data_fetcher.place_order(
                symbol=self.symbol,
                side=side,
                qty=self.quantity,
                current_price=current_price,
                leverage=self.leverage,
                stop_loss=stop_loss,
                take_profit=take_profit
            )

            if order_result:
                print(f"Order successfully placed: {order_result}")
                self.open_order_time = time.time()  # Set the time when the order was placed
            else:
                print("Failed to place order.")
        else:
            print("No suitable signals for position opening.")

    def run(self):
        self.job()
        schedule.every(10).seconds.do(self.job)
        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    bot = TradingBot()
    bot.run()
