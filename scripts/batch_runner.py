import sys
import os
import argparse
import pandas as pd
from datetime import datetime

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from kairo.src.data_loader import fetch_data
from kairo.src.strategy import (
    RSIStrategy, 
    EMACrossoverStrategy, 
    BollingerReversionStrategy,
    MACDStrategy,
    StochasticRSIStrategy,
    GoldenRSIStrategy,
    DiamondRSIStrategy,
    BollingerSqueezeStrategy
)
from kairo.src.backtester import Backtester
from kairo.src.plotting import plot_backtest_results
from kairo.src.universe import NIFTY_50_TICKERS

# Try to import tabulate for pretty printing
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

NIFTY_SECTOR_LEADERS = [
    'RELIANCE.NS', 'HDFCBANK.NS', 'INFY.NS', 'TCS.NS', 'ICICIBANK.NS', 
    'TATAMOTORS.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS', 'LT.NS'
]

def get_strategy(strategy_name):
    if strategy_name.upper() == 'RSI':
        return RSIStrategy(period=14, buy_threshold=30, sell_threshold=70)
    elif strategy_name.upper() == 'EMA':
        return EMACrossoverStrategy(short_window=9, long_window=21)
    elif strategy_name.upper() == 'BOLLINGER':
        return BollingerReversionStrategy(period=20, dev=2)
    elif strategy_name.upper() == 'MACD':
        return MACDStrategy()
    elif strategy_name.upper() == 'STOCHRSI':
        return StochasticRSIStrategy()
    elif strategy_name.upper() == 'GOLDEN_RSI':
        return GoldenRSIStrategy()
    elif strategy_name.upper() == 'DIAMOND_RSI':
        return DiamondRSIStrategy()
    elif strategy_name.upper() == 'BOLLINGER_SQUEEZE':
        return BollingerSqueezeStrategy()
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

def run_batch(strategy_name, interval='15m', universe_name='NIFTY50'):
    print(f"Starting Batch Backtest for Strategy: {strategy_name.upper()}")
    print(f"Interval: {interval}, Universe: {universe_name}")
    print("-" * 50)
    
    results = []
    
    strategy_class = get_strategy(strategy_name)
    backtester = Backtester(initial_capital=10000, commission=0.0015)
    
    # Select Universe
    if universe_name.upper() == 'NIFTY50':
        ticker_list = NIFTY_50_TICKERS
    elif universe_name.upper() == 'TEST':
        ticker_list = NIFTY_SECTOR_LEADERS 
    else:
        # Fallback to test if unknown
        print(f"Unknown universe '{universe_name}', defaulting to TEST.")
        ticker_list = NIFTY_SECTOR_LEADERS

    # Determine Period based on Interval
    if interval in ['5m', '15m']:
        period = '59d'
    elif interval == '1h':
        period = '700d' # Approx 2 years
    elif interval == '1d':
        period = '10y' # Max history
    else:
        period = '59d' # Default fallback
    
    # Initialize timestamp early for report filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = os.path.join(current_dir, 'reports')
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    consolidated_report_content = []
    
    for ticker in ticker_list:
        try:
            # Fetch data 
            df = fetch_data(ticker, period=period, interval=interval)
            
            if df.empty:
                print(f"[!] {ticker}: No data found.")
                continue
                
            # Run backtest
            metrics = backtester.run(df, strategy_class)
            
            roi = metrics['ROI (%)']
            max_dd = metrics['Max Drawdown (%)']
            
            # Simple progress log
            print(f"[+] {ticker}: {roi:.2f}%")
            
            results.append({
                'Ticker': ticker,
                'Return (%)': round(metrics['ROI (%)'], 2),
                'Max Drawdown (%)': round(metrics['Max Drawdown (%)'], 2),
                'Final Value (INR)': round(metrics['Final Value'], 2)
            })

            # --- Generate Plot Only ---
            plot_path = plot_backtest_results(
                df, 
                metrics['Equity Curve'], 
                metrics['Trades'], 
                ticker, 
                strategy_name, 
                reports_dir
            )
            rel_plot_path = os.path.basename(plot_path)

            # --- Accumulate Markdown Content ---
            ticker_md = ""
            ticker_md += f"## {ticker}\n"
            ticker_md += f"**Return**: {metrics['ROI (%)']:.2f}% | **Max DD**: {metrics['Max Drawdown (%)']:.2f}% | **Trades**: {len(metrics['Trades'])}\n\n"
            ticker_md += f"![{ticker}]({rel_plot_path})\n\n"
            
            if metrics['Trades']:
                ticker_md += "### Recent Trades\n"
                ticker_md += "| Date | Type | Price | Shares | Value |\n"
                ticker_md += "| :--- | :--- | :--- | :--- | :--- |\n"
                for t in metrics['Trades'][-5:]: # Show last 5
                     ticker_md += f"| {t['Date']} | {t['Type']} | {t['Price']:.2f} | {t['Shares']} | {t['Value']:.0f} |\n"
            else:
                 ticker_md += "*No trades executed.*\n"
            
            ticker_md += "\n---\n\n"
            consolidated_report_content.append(ticker_md)
            
            # -------------------------------
            
        except Exception as e:
            print(f"[!] {ticker}: Failed with error {str(e)}")
            
    # Process Results
    if not results:
        print("No results generated.")
        return

    results_df = pd.DataFrame(results)
    results_df.sort_values(by='Return (%)', ascending=False, inplace=True)
    
    # Save CSV
    # Save CSV
    csv_filename = f"batch_results_{strategy_name.lower()}_{interval}_{timestamp}.csv"
    csv_filepath = os.path.join(reports_dir, csv_filename)
    results_df.to_csv(csv_filepath, index=False)
    
    # Save Consolidated Markdown Report
    md_filename = f"batch_report_{strategy_name.lower()}_{interval}_{timestamp}.md"
    md_filepath = os.path.join(reports_dir, md_filename)
    
    avg_return = results_df['Return (%)'].mean()
    
    with open(md_filepath, 'w') as f:
        f.write(f"# Batch Report: {strategy_name.upper()} ({interval})\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Universe**: {universe_name} | **Average ROI**: {avg_return:.2f}%\n\n")
        
        f.write("## Summary Table\n")
        # Use tabulate for cleaner markdown table if available, else simple pipe
        if HAS_TABULATE:
            f.write(tabulate(results_df, headers='keys', tablefmt='github', showindex=False))
        else:
            f.write(results_df.to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## Detailed Analysis\n\n")
        for content in consolidated_report_content:
            f.write(content)
            
    print("-" * 50)
    print("-" * 50)
    print(f"Batch completed.\nCSV: {csv_filepath}\nReport: {md_filepath}")
    print(f"Average ROI: {avg_return:.2f}%")
    print("-" * 50)
    
    # Print Table
    if HAS_TABULATE:
        print(tabulate(results_df, headers='keys', tablefmt='psql', showindex=False))
    else:
        print(results_df.to_string(index=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run batch backtest for Indian Stocks')
    parser.add_argument('--strategy', type=str, required=True, 
                        choices=['RSI', 'EMA', 'BOLLINGER', 'MACD', 'STOCHRSI', 'GOLDEN_RSI', 'DIAMOND_RSI', 'BOLLINGER_SQUEEZE'],
                        help='Strategy to run (RSI, EMA, BOLLINGER, MACD, STOCHRSI, GOLDEN_RSI, DIAMOND_RSI, BOLLINGER_SQUEEZE)')
    
    parser.add_argument('--interval', type=str, default='15m',
                        choices=['5m', '15m', '1h', '1d'],
                        help='Time interval (5m, 15m, 1h, 1d)')
    parser.add_argument('--universe', type=str, default='NIFTY50',
                        help='Stock Universe (NIFTY50, TEST)')
    
    args = parser.parse_args()
    
    run_batch(args.strategy, args.interval, args.universe)
