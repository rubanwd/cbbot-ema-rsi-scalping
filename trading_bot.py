# trading_bot.py

import schedule
import time
import logging
from data_fetcher import DataFetcher
from indicators import Indicators  # Add this import
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
        self.risk_management = RiskManagement(
            atr_multiplier=float(os.getenv("ATR_MULTIPLIER", 1.0)),
            risk_ratio=float(os.getenv("RISK_RATIO", 1.0))
        )
        self.symbol = os.getenv("TRADING_SYMBOL", 'BTCUSDT')
        self.quantity = float(os.getenv("TRADE_QUANTITY", 0.03))

        # Load trading parameters
        self.interval = os.getenv("TRADING_INTERVAL", '1')  # Changed to 1-minute interval for quicker trades
        self.limit = int(os.getenv("TRADING_LIMIT", 100))  # Number of candles for analysis

        self.leverage = int(os.getenv("LEVERAGE", 10))  # Default leverage is set to 10 if not provided

        # Load strategy switches
        self.enable_ema_rsi_strategy = os.getenv("ENABLE_EMA_RSI_STRATEGY", "True").lower() == "true"

        # Set up logging
        logging.basicConfig(filename='trading_bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
    def job(self):
        print("--------------------------------------")

        # Check for open positions
        open_positions = self.data_fetcher.get_open_positions(self.symbol)
        if open_positions and len(open_positions) > 0:
            print("There is already an open position. A new order will not be placed.")
            return

        # Check for open limit orders and cancel if necessary
        open_orders = self.data_fetcher.get_open_orders(self.symbol)
        if open_orders and len(open_orders) > 0:
            print("There is an open limit order. A new order will not be placed.")
            return
        
        # Check the last closed position
        last_closed_position = self.data_fetcher.get_last_closed_position(self.symbol)

        if last_closed_position:
            last_closed_time = int(last_closed_position['updatedTime']) / 1000
            current_time = time.time()
            time_since_last_close = current_time - last_closed_time
            print(f"Time since last closed position: {int(time_since_last_close)} seconds")

            if time_since_last_close < 180:  # 180 seconds = 3 minutes
                print("The last closed position was less than 3 minutes ago. A new order will not be placed.")
                return
            else:
                print("More than 3 minutes have passed since the last closed position.")

        # Retrieve historical data
        get_historical_data = self.data_fetcher.get_historical_data(self.symbol, self.interval, self.limit)
        if get_historical_data is None:
            print("Failed to retrieve historical data.")
            return

        df = pd.DataFrame(get_historical_data)
        df.columns = ["timestamp", "open", "high", "low", "close", "volume", "turnover"]
        df['close'] = df['close'].astype(float)

        current_price = self.data_fetcher.get_real_time_price(self.symbol)
        if current_price is None:
            print("Failed to retrieve real-time price.")
            return

        print(f"current_price ----: {current_price}")

        trend = None

        # Evaluate EMA + RSI strategy if enabled
        ema_rsi_trend = self.strategy.ema_rsi_strategy(get_historical_data)
        if ema_rsi_trend:
            trend = ema_rsi_trend
            print(f"EMA + RSI Strategy Signal: {trend.upper()}")

        if trend:
            print(f"Signal for position: {trend.upper()}")

            # Risk management with dynamic ATR-based calculation
            stop_loss, take_profit = self.risk_management.calculate_risk_management(current_price, trend, df)
            print(f"Stop Loss: {stop_loss:.2f}")
            print(f"Take Profit: {take_profit:.2f}")

            side = 'Buy' if trend == 'long' else 'Sell'

            print(f"Order side: {side}")

            # Place order
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
            else:
                print("Failed to place order.")
        else:
            print("No suitable signals for position opening.")

    def run(self):
        self.job()
        schedule.every(10).seconds.do(self.job)
        print("Trading bot launched and ready to work.")
        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    try:
        bot = TradingBot()
        bot.run()
    except Exception as e:
        print(f"Error starting trading bot: {e}")

