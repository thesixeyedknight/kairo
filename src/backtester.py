import pandas as pd
import numpy as np

class Backtester:
    def __init__(self, initial_capital=10000, commission=0.0015, trailing_stop_pct=None):
        self.initial_capital = initial_capital
        self.commission = commission
        self.trailing_stop_pct = trailing_stop_pct

    def run(self, df: pd.DataFrame, strategy) -> dict:
        """
        Runs the backtest.
        Executes trades on the NEXT Open based on CURRENT Signal.
        """
        # Apply strategy to get signals
        df = strategy.generate_signals(df)
        
        cash = self.initial_capital
        position = 0 # Number of shares
        portfolio_values = []
        trades = []
        highest_price = 0.0 # Track highest price for trailing stop
        
        # Iterate through the DataFrame
        # We need to look at i for Signal and i+1 for Execution Price (Open)
        
        for i in range(len(df) - 1):
            current_signal = df['Signal'].iloc[i]
            next_open = df['Open'].iloc[i+1]
            trade_date = df.index[i+1]
            trade_date = df.index[i+1]
            
            # --- Trailing Stop Logic ---
            if self.trailing_stop_pct is not None and position > 0:
                # Update highest price since entry
                # Current bar (i) High is available.
                # However, we are making decisions for i+1 Open based on i Close/Signal.
                # If we use i High, we are effectively checking if Stop was hit TODAY.
                # If hit, we sell at Stop Price.
                
                current_high = df['High'].iloc[i]
                current_low = df['Low'].iloc[i]
                
                if current_high > highest_price:
                    highest_price = current_high
                    
                stop_price = highest_price * (1 - self.trailing_stop_pct)
                
                if current_low < stop_price:
                    # Stop Hit!
                    # Execution Price: Stop Price (slippage not modeled, but realistic worst case)
                    # Or do we sell at Close? Stop usually triggers strictly.
                    exec_price = stop_price
                    
                    revenue = position * exec_price
                    comm = revenue * self.commission
                    cash += (revenue - comm)
                    trades.append({
                        'Date': df.index[i], # Hit today
                        'Type': 'Sell (Trailing Stop)',
                        'Price': exec_price,
                        'Shares': position,
                        'Value': revenue,
                        'Commission': comm
                    })
                    position = 0
                    highest_price = 0.0
                    current_signal = 0 # Cancel any other signal for continuity
            
            # HANDLING SCALAR VALUES CORRECTLY
            if isinstance(next_open, pd.Series):
                next_open = next_open.item()
            
            if current_signal == 1:
                # Buy Logic
                if position == 0:
                    # Buy as much as possible
                    shares_to_buy = int(cash / next_open)
                    if shares_to_buy > 0:
                        cost = shares_to_buy * next_open
                        comm = cost * self.commission
                        if cash >= cost + comm:
                            cash -= (cost + comm)
                            position += shares_to_buy
                            trades.append({
                                'Date': trade_date,
                                'Type': 'Buy',
                                'Price': next_open,
                                'Shares': shares_to_buy,
                                'Value': cost,
                                'Commission': comm
                            })
                            # Reset highest price for new position
                            highest_price = next_open
            
            elif current_signal == -1:
                # Sell Logic
                if position > 0:
                    # Sell all
                    revenue = position * next_open
                    comm = revenue * self.commission
                    cash += (revenue - comm)
                    trades.append({
                        'Date': trade_date,
                        'Type': 'Sell',
                        'Price': next_open,
                        'Shares': position,
                        'Value': revenue,
                        'Commission': comm
                    })
                    position = 0
                    highest_price = 0.0
            
            # Calculate daily portfolio value (Cash + Position Value at Close)
            current_close = df['Close'].iloc[i+1]
            if isinstance(current_close, pd.Series):
                current_close = current_close.item()
                
            current_value = cash + (position * current_close)
            portfolio_values.append(current_value)
            
            if current_value <= 0:
                print(f"WARNING: Bankruptcy detected! Current Value: {current_value} on {trade_date}")
            
        # Metrics
        final_value = portfolio_values[-1] if portfolio_values else self.initial_capital
        roi = (final_value - self.initial_capital) / self.initial_capital * 100
        
        # Calculate max drawdown
        portfolio_series = pd.Series(portfolio_values, index=df.index[1:])
        rolling_max = portfolio_series.cummax()
        drawdown = (portfolio_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100 if not drawdown.empty else 0.0
        
        return {
            "Initial Capital": self.initial_capital,
            "Final Value": final_value,
            "ROI (%)": roi,
            "Max Drawdown (%)": max_drawdown,
            "Equity Curve": portfolio_values,
            "Trades": trades,
            "Signals": df['Signal']
        }
