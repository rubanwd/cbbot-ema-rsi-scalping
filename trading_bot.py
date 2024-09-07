# trading_bot.py

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
            risk_ratio=float(os.getenv("RISK_RATIO", 1.0))
        )
        self.symbol = os.getenv("TRADING_SYMBOL", 'BTCUSDT')
        self.quantity = float(os.getenv("TRADE_QUANTITY", 0.03))

        # Load trading parameters
        self.interval = os.getenv("TRADING_INTERVAL", '1')
        self.limit = int(os.getenv("TRADING_LIMIT", 100))
        self.leverage = int(os.getenv("LEVERAGE", 10))

        # Load strategy switches
        self.enable_ema_rsi_strategy = os.getenv("ENABLE_EMA_RSI_STRATEGY", "True").lower() == "true"

        # Set up logging
        logging.basicConfig(filename='trading_bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
    def job(self):
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
        df['EMA_9'] = self.indicators.calculate_ema(df, 9)
        df['EMA_21'] = self.indicators.calculate_ema(df, 21)
        df['RSI'] = self.indicators.calculate_rsi(df, 14)
        df['MACD'], df['MACD_signal'] = self.indicators.calculate_macd(df)
        df['Stochastic'], df['Stochastic_signal'] = self.indicators.calculate_stochastic(df)
        df['Bollinger_upper'], df['Bollinger_middle'], df['Bollinger_lower'] = self.indicators.calculate_bollinger_bands(df)

        # Get the latest indicator values
        ema_9 = df['EMA_9'].iloc[-1]
        ema_21 = df['EMA_21'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        macd = df['MACD'].iloc[-1]
        macd_signal = df['MACD_signal'].iloc[-1]
        stochastic = df['Stochastic'].iloc[-1]
        stochastic_signal = df['Stochastic_signal'].iloc[-1]
        bollinger_upper = df['Bollinger_upper'].iloc[-1]
        bollinger_middle = df['Bollinger_middle'].iloc[-1]
        bollinger_lower = df['Bollinger_lower'].iloc[-1]

        # Print the indicator values
        print(f"EMA 9: {ema_9:.2f}")
        print(f"EMA 21: {ema_21:.2f}")
        print(f"RSI: {rsi:.2f}")
        print(f"MACD: {macd:.2f}")
        print(f"MACD Signal: {macd_signal:.2f}")
        print(f"Stochastic: {stochastic:.2f}")
        print(f"Stochastic Signal: {stochastic_signal:.2f}")
        print(f"Bollinger Upper: {bollinger_upper:.2f}")
        print(f"Bollinger Middle: {bollinger_middle:.2f}")
        print(f"Bollinger Lower: {bollinger_lower:.2f}")

        open_positions = self.data_fetcher.get_open_positions(self.symbol)
        if open_positions:
            print("There is already an open position. A new order will not be placed.")
            return

        open_orders = self.data_fetcher.get_open_orders(self.symbol)
        if open_orders:
            print("There is an open limit order. A new order will not be placed.")
            return

        current_price = self.data_fetcher.get_real_time_price(self.symbol)
        if current_price is None:
            print("Failed to retrieve real-time price.")
            return

        print(f"Current Price: {current_price:.2f}")

        trend = self.strategy.combine_indicators_strategy(df)
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
