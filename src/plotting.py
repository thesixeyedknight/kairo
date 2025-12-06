import matplotlib.pyplot as plt
import pandas as pd
import os

def plot_backtest_results(df, equity_curve, trades, ticker, strategy_name, output_dir):
    """
    Generates a plot with Price (Buy/Sell signals) and Equity Curve.
    Saves to output_dir.
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Prepare Data
    # Align equity curve index with df index (shifted by 1 as equity is calculated at i+1)
    equity_series = pd.Series(equity_curve, index=df.index[1:])
    
    # Create Figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    
    # Plot Price
    ax1.plot(df.index, df['Close'], label='Close Price', color='#1f77b4', linewidth=1)
    
    # Plot Buy/Sell Markers
    buy_trades = [t for t in trades if t['Type'] == 'Buy']
    sell_trades = [t for t in trades if t['Type'] == 'Sell']
    
    if buy_trades:
        buy_dates = [t['Date'] for t in buy_trades]
        buy_prices = [t['Price'] for t in buy_trades]
        ax1.scatter(buy_dates, buy_prices, marker='^', color='green', label='Buy', s=100, zorder=5)
        
    if sell_trades:
        sell_dates = [t['Date'] for t in sell_trades]
        sell_prices = [t['Price'] for t in sell_trades]
        ax1.scatter(sell_dates, sell_prices, marker='v', color='red', label='Sell', s=100, zorder=5)
        
    ax1.set_title(f'{ticker} - {strategy_name} Performance')
    ax1.set_ylabel('Price (INR)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot Equity Curve
    ax2.plot(equity_series.index, equity_series, label='Portfolio Value (Equity)', color='#2ca02c', linewidth=1.5)
    ax2.fill_between(equity_series.index, equity_series, alpha=0.1, color='#2ca02c')
    ax2.set_ylabel('Equity (INR)')
    ax2.set_xlabel('Date')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Format and Save
    plt.tight_layout()
    filename = f"{ticker}_{strategy_name}_plot.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath)
    plt.close()
    
    return filepath
