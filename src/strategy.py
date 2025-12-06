from abc import ABC, abstractmethod
import pandas as pd
import talib

class TradingStrategy(ABC):
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Takes a DataFrame with OHLCV data and appends a 'Signal' column.
        Signal: 1 (Buy), -1 (Sell), 0 (Hold).
        """
        pass

class RSIStrategy(TradingStrategy):
    def __init__(self, period=14, buy_threshold=30, sell_threshold=70):
        self.period = period
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates signals using RSI.
        """
        df = df.copy()
        
        # Ensure 'Close' is available and 1D
        close = df['Close']
        if isinstance(close, pd.DataFrame):
            # If multiple columns or multiindex, try to handle or raise error
            # Assuming simple single-ticker DF from data_loader
            if close.shape[1] == 1:
                close = close.iloc[:, 0]
            else:
                 raise ValueError("DataFrame 'Close' column is not 1D Series")

        rsi = talib.RSI(close.values, timeperiod=self.period)
        df['RSI'] = rsi
        
        # Initialize Signal column
        df['Signal'] = 0
        
        # Vectorized signal assignment
        df.loc[df['RSI'] < self.buy_threshold, 'Signal'] = 1
        df.loc[df['RSI'] > self.sell_threshold, 'Signal'] = -1
        
        # Note: This is raw signal generation based on indicators.
        # Position management (holding until exit signal) is handled by the backtester or logic below.
        # Requirement: "Signal = 1 if RSI < 30, Signal = -1 if RSI > 70, else 0"
        # This implies a simple signal per bar. The backtester should interpret this.
        # Usually, one buys on 1 and holds until -1? Or buys every time it's < 30?
        # Standard interpretation: 1 is "Entry Long", -1 is "Entry Short" or "Exit Long".
        # Let's stick to the prompt's definition of the Signal column.
        
        return df

class EMACrossoverStrategy(TradingStrategy):
    def __init__(self, short_window=9, long_window=21):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates buy/sell signals based on EMA crossover.
        """
        df = df.copy()
        
        # Ensure 'Close' is available and 1D
        close = df['Close']
        if isinstance(close, pd.DataFrame):
            if close.shape[1] == 1:
                close = close.iloc[:, 0]
            else:
                 raise ValueError("DataFrame 'Close' column is not 1D Series")
                 
        # Calculate EMAs
        df['EMA_Short'] = talib.EMA(close.values, timeperiod=self.short_window)
        df['EMA_Long'] = talib.EMA(close.values, timeperiod=self.long_window)
        
        df['Signal'] = 0
        
        # Crossover Logic
        # Buy: Short crosses above Long
        # Sell: Short crosses below Long
        # We need to look at previous row to detect the cross
        
        short_ema = df['EMA_Short']
        long_ema = df['EMA_Long']
        
        # Shift to get previous values
        prev_short = short_ema.shift(1)
        prev_long = long_ema.shift(1)
        
        # Buy Signal (Golden Cross)
        buy_condition = (prev_short < prev_long) & (short_ema > long_ema)
        df.loc[buy_condition, 'Signal'] = 1
        
        # Sell Signal (Death Cross)
        sell_condition = (prev_short > prev_long) & (short_ema < long_ema)
        df.loc[sell_condition, 'Signal'] = -1
        
        return df

class BollingerReversionStrategy(TradingStrategy):
    def __init__(self, period=20, dev=2):
        self.period = period
        self.dev = dev

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates mean reversion signals based on Bollinger Bands.
        """
        df = df.copy()
        
        # Ensure 'Close' is available and 1D
        close = df['Close']
        if isinstance(close, pd.DataFrame):
            if close.shape[1] == 1:
                close = close.iloc[:, 0]
            else:
                 raise ValueError("DataFrame 'Close' column is not 1D Series")
                 
        # Calculate Bollinger Bands
        upper, middle, lower = talib.BBANDS(close.values, timeperiod=self.period, nbdevup=self.dev, nbdevdn=self.dev, matype=0)
        
        df['BB_Upper'] = upper
        df['BB_Lower'] = lower
        
        df['Signal'] = 0
        
        # Reversion Logic
        # Buy: Price < Lower Band (Oversold)
        # Sell: Price > Upper Band (Overbought)
        
        # Note: This strategy buys as long as price is below lower band.
        # A more refined version might wait for price to cross back inside, 
        # but let's stick to the prompt: "Signal = 1 if Close < Lower Band"
        
        df.loc[close < lower, 'Signal'] = 1
        df.loc[close > upper, 'Signal'] = -1
        
        return df

class MACDStrategy(TradingStrategy):
    def __init__(self, fast=12, slow=26, signal=9):
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates buy/sell signals based on MACD crossover.
        """
        df = df.copy()
        
        # Ensure 'Close' is available and 1D
        close = df['Close']
        if isinstance(close, pd.DataFrame):
            if close.shape[1] == 1:
                close = close.iloc[:, 0]
            else:
                 raise ValueError("DataFrame 'Close' column is not 1D Series")
                 
        # Calculate MACD
        macd, macdsignal, macdhist = talib.MACD(close.values, fastperiod=self.fast, slowperiod=self.slow, signalperiod=self.signal)
        
        df['MACD'] = macd
        df['MACD_Signal'] = macdsignal
        
        df['Signal'] = 0
        
        # Crossover Logic
        prev_macd = df['MACD'].shift(1)
        prev_signal = df['MACD_Signal'].shift(1)
        
        # Buy Signal (Golden Cross)
        buy_condition = (prev_macd < prev_signal) & (df['MACD'] > df['MACD_Signal'])
        df.loc[buy_condition, 'Signal'] = 1
        
        # Sell Signal (Death Cross)
        sell_condition = (prev_macd > prev_signal) & (df['MACD'] < df['MACD_Signal'])
        df.loc[sell_condition, 'Signal'] = -1
        
        return df

class StochasticRSIStrategy(TradingStrategy):
    def __init__(self, timeperiod=14, fastk_period=5, fastd_period=3):
        self.timeperiod = timeperiod
        self.fastk_period = fastk_period
        self.fastd_period = fastd_period

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates signals based on Stochastic RSI.
        """
        df = df.copy()
        
        # Ensure 'Close' is available and 1D
        close = df['Close']
        if isinstance(close, pd.DataFrame):
            if close.shape[1] == 1:
                close = close.iloc[:, 0]
            else:
                 raise ValueError("DataFrame 'Close' column is not 1D Series")
                 
        # Calculate Stochastic RSI
        fastk, fastd = talib.STOCHRSI(close.values, timeperiod=self.timeperiod, fastk_period=self.fastk_period, fastd_period=self.fastd_period, fastd_matype=0)
        
        df['FastK'] = fastk
        df['FastD'] = fastd
        
        df['Signal'] = 0
        
        prev_k = df['FastK'].shift(1)
        prev_d = df['FastD'].shift(1)
        
        # Buy Logic: Oversold (K < 20) AND K crosses above D
        # Condition for cross: prev_k < prev_d AND cur_k > cur_d
        buy_condition = (df['FastK'] < 20) & (prev_k < prev_d) & (df['FastK'] > df['FastD'])
        df.loc[buy_condition, 'Signal'] = 1
        
        # Sell Logic: Overbought (K > 80) AND K crosses below D
        # Condition for cross: prev_k > prev_d AND cur_k < cur_d
        sell_condition = (df['FastK'] > 80) & (prev_k > prev_d) & (df['FastK'] < df['FastD'])
        df.loc[sell_condition, 'Signal'] = -1
        
        return df

class GoldenRSIStrategy(TradingStrategy):
    def __init__(self, rsi_period=14, ema_filter=200, stop_loss_pct=0.01, take_profit_pct=0.02):
        self.rsi_period = rsi_period
        self.ema_filter = ema_filter
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates signals for Golden RSI Strategy.
        Buy: Uptrend (Close > EMA200) + Oversold (RSI < 30).
        Sell: Mean Reversion (RSI > 50) or Trend Reversal (Close < EMA200 & RSI > 70).
        """
        df = df.copy()
        
        # Ensure 'Close' is available and 1D
        close = df['Close']
        if isinstance(close, pd.DataFrame):
            if close.shape[1] == 1:
                close = close.iloc[:, 0]
            else:
                 raise ValueError("DataFrame 'Close' column is not 1D Series")
                 
        # Calculate Indicators
        df['RSI'] = talib.RSI(close.values, timeperiod=self.rsi_period)
        df['EMA_Filter'] = talib.EMA(close.values, timeperiod=self.ema_filter)
        
        df['Signal'] = 0
        
        # Logic:
        # Buy (1): Close > EMA_Filter AND RSI < 30
        # Sell (-1): RSI > 50 (Mean Reversion Exit)
        
        # Note: We prioritize Sell over Buy if both happen (impossible given RSI ranges)
        
        # Buy Condition
        buy_condition = (close > df['EMA_Filter']) & (df['RSI'] < 30)
        df.loc[buy_condition, 'Signal'] = 1
        
        # Sell Condition (Aggressive Mean Reversion Exit)
        sell_condition = (df['RSI'] > 50)
        df.loc[sell_condition, 'Signal'] = -1
        
        return df

class DiamondRSIStrategy(TradingStrategy):
    def __init__(self, rsi_period=14, ema_trend=200, atr_period=14, min_volatility=0.002):
        self.rsi_period = rsi_period
        self.ema_trend = ema_trend
        self.atr_period = atr_period
        self.min_volatility = min_volatility

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates signals for Diamond RSI Strategy (High Volatility).
        Filter: ATR > (Close * min_volatility)
        Buy: Uplift (Close > EMA) + Dip (RSI < 30) + Volatility.
        Sell: Overbought (RSI > 70).
        """
        df = df.copy()
        
        # Ensure 'Close', 'High', 'Low' are available
        # We need High/Low/Close for ATR
        close = df['Close']
        high = df['High']
        low = df['Low']
        
        # Calculate Indicators
        df['RSI'] = talib.RSI(close.values, timeperiod=self.rsi_period)
        df['EMA_Trend'] = talib.EMA(close.values, timeperiod=self.ema_trend)
        df['ATR'] = talib.ATR(high.values, low.values, close.values, timeperiod=self.atr_period)
        
        df['Signal'] = 0
        
        # Volatility Filter
        # True if ATR is significant enough
        vol_filter = df['ATR'] > (close * self.min_volatility)
        
        # Logic:
        # Buy (1): Close > EMA AND RSI < 30 AND Vol_Filter
        buy_condition = (close > df['EMA_Trend']) & (df['RSI'] < 30) & vol_filter
        df.loc[buy_condition, 'Signal'] = 1
        
        # Sell (-1): RSI > 70 OR (Close < EMA AND RSI > 70 - Short entry logic mapped to exit/sell)
        sell_condition = (df['RSI'] > 70)
        df.loc[sell_condition, 'Signal'] = -1
        
        return df

class KairoLiveStrategy(TradingStrategy):
    def __init__(self, rsi_period=14, ema_trend=200, hard_stop_pct=0.02):
        self.rsi_period = rsi_period
        self.ema_trend = ema_trend
        self.hard_stop_pct = hard_stop_pct

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates signals for Kairo Live Trading.
        Buy: Trend Up (Close > EMA) + Dip (RSI < 30).
        Sell: Trend Down (Close < EMA) + Spike (RSI > 70).
        
        Exits ( Mean Reversion ):
        - Exit Buy: RSI > 70.
        - Exit Sell: RSI < 30.
        """
        df = df.copy()
        
        # Ensure 'Close' is available and 1D
        close = df['Close']
        if isinstance(close, pd.DataFrame):
            if close.shape[1] == 1:
                close = close.iloc[:, 0]
            else:
                 raise ValueError("DataFrame 'Close' column is not 1D Series")

        # Calculate Indicators
        df['RSI'] = talib.RSI(close.values, timeperiod=self.rsi_period)
        df['EMA_Trend'] = talib.EMA(close.values, timeperiod=self.ema_trend)
        
        df['Signal'] = 0

        # Buy Signal (Entry)
        df.loc[(close > df['EMA_Trend']) & (df['RSI'] < 30), 'Signal'] = 1
        
        # Sell Signal (Exit / Short Entry)
        df.loc[df['RSI'] > 70, 'Signal'] = -1

        return df

class BollingerSqueezeStrategy(TradingStrategy):
    def __init__(self, window=20, std_dev=2.0, squeeze_threshold=0.10):
        self.window = window
        self.std_dev = std_dev
        self.squeeze_threshold = squeeze_threshold

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates signals for Bollinger Band Squeeze.
        Squeeze: BandWidth < threshold.
        Buy: Squeeze + Breakout Up (Close > Upper).
        Sell: Breakout Down (Close < Lower) OR Exit (Close < Middle).
        """
        df = df.copy()
        
        # Ensure 'Close' is available and 1D
        close = df['Close']
        if isinstance(close, pd.DataFrame):
            if close.shape[1] == 1:
                close = close.iloc[:, 0]
            else:
                 raise ValueError("DataFrame 'Close' column is not 1D Series")

        # Calculate Bollinger Bands
        # Note: talib.BBANDS returns Upper, Middle, Lower
        upper, middle, lower = talib.BBANDS(close.values, timeperiod=self.window, nbdevup=self.std_dev, nbdevdn=self.std_dev, matype=0)
        
        df['BB_Upper'] = upper
        df['BB_Middle'] = middle
        df['BB_Lower'] = lower
        
        # Calculate BandWidth
        # Avoid division by zero (though Middle usually > 0 for stocks)
        df['BandWidth'] = (upper - lower) / middle
        
        df['Signal'] = 0
        
        # Conditions
        squeeze = df['BandWidth'] < self.squeeze_threshold
        
        breakout_up = (close > upper)
        breakout_down = (close < lower)
        
        # Exit Condition (Mean Reversion / Trend Break)
        # Close below Middle Band (Moving Average)
        below_ma = (close < middle)
        
        # Signal Generation
        
        # Buy Entry: Squeeze AND Breakout Up
        buy_condition = squeeze & breakout_up
        df.loc[buy_condition, 'Signal'] = 1
        
        # Sell/Exit:
        # 1. Squeeze Breakdown (Short Entry)
        # 2. Mean Reversion Exit (Long Exit)
        
        # Note: In Long-Only Backtester, -1 exits position.
        sell_condition = (squeeze & breakout_down) | below_ma
        df.loc[sell_condition, 'Signal'] = -1
        
        return df
