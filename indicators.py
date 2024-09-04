# indicators.py

class Indicators:
    @staticmethod
    def calculate_ema(df, span):
        return df['close'].ewm(span=span, adjust=False).mean()

    @staticmethod
    def calculate_rsi(df, period=14):
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_macd(df):
        short_ema = df['close'].ewm(span=12, adjust=False).mean()
        long_ema = df['close'].ewm(span=26, adjust=False).mean()
        macd = short_ema - long_ema
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        return macd, macd_signal

    @staticmethod
    def calculate_stochastic(df, period=14):
        high_14 = df['high'].rolling(window=period).max()
        low_14 = df['low'].rolling(window=period).min()
        k_percent = 100 * ((df['close'] - low_14) / (high_14 - low_14))
        d_percent = k_percent.rolling(window=3).mean()
        return k_percent, d_percent

    @staticmethod
    def calculate_bollinger_bands(df, window=20):
        middle_band = df['close'].rolling(window=window).mean()
        std_dev = df['close'].rolling(window=window).std()
        upper_band = middle_band + (std_dev * 2)
        lower_band = middle_band - (std_dev * 2)
        return upper_band, middle_band, lower_band

