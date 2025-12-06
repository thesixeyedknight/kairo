import sys
import os
import argparse
from datetime import datetime

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from kairo.src.data_loader import fetch_data
from kairo.src.strategy import (
    RSIStrategy, 
    EMACrossoverStrategy, 
    BollingerReversionStrategy
)
from kairo.src.backtester import Backtester
from kairo.src.plotting import plot_backtest_results

def get_strategy(strategy_name):
    if strategy_name.upper() == 'RSI':
        return RSIStrategy(period=14, buy_threshold=30, sell_threshold=70)
    elif strategy_name.upper() == 'EMA':
        return EMACrossoverStrategy(short_window=9, long_window=21)
    elif strategy_name.upper() == 'BOLLINGER':
        return BollingerReversionStrategy(period=20, dev=2)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

def generate_report(ticker, strategy_name):
    print(f"Generating Report for {ticker} with {strategy_name}...")
    
    # 1. Fetch Data
    df = fetch_data(ticker, period='59d', interval='5m')
    if df.empty:
        print("Data fetch failed.")
        return

    # 2. Run Backtest
    strategy = get_strategy(strategy_name)
    backtester = Backtester(initial_capital=100000, commission=0.001)
    results = backtester.run(df, strategy)
    
    # 3. Generate Plot
    reports_dir = os.path.normpath(os.path.join(current_dir, 'reports'))
    plot_path = plot_backtest_results(
        df, 
        results['Equity Curve'], 
        results['Trades'], 
        ticker, 
        strategy_name, 
        reports_dir
    )
    
    # 4. Generate Markdown
    # Relative path for the image link in markdown
    rel_plot_path = os.path.basename(plot_path)
    
    md_filename = f"{ticker}_{strategy_name}_report.md"
    md_filepath = os.path.join(reports_dir, md_filename)
    
    with open(md_filepath, 'w') as f:
        f.write(f"# Backtest Report: {ticker} ({strategy_name})\n\n")
        f.write(f"**Date Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Performance Overview\n")
        f.write("| Metric | Value |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| **Final Equity** | ₹{results['Final Value']:.2f} |\n")
        f.write(f"| **Return (ROI)** | {results['ROI (%)']:.2f}% |\n")
        f.write(f"| **Max Drawdown** | {results['Max Drawdown (%)']:.2f}% |\n")
        f.write(f"| **Total Trades** | {len(results['Trades'])} |\n\n")
        
        f.write("## Equity & Signals\n")
        f.write(f"![{ticker} Performance]({rel_plot_path})\n\n")
        
        f.write("## Recent Trades\n")
        if results['Trades']:
            f.write("| Date | Type | Price | Shares | Value | Commission |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
            # Show last 10 trades
            for t in results['Trades'][-10:]:
                f.write(f"| {t['Date']} | {t['Type']} | ₹{t['Price']:.2f} | {t['Shares']} | ₹{t['Value']:.2f} | ₹{t['Commission']:.2f} |\n")
        else:
            f.write("No trades executed.\n")
            
    print(f"Report generated: {md_filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate detailed backtest report')
    parser.add_argument('--ticker', type=str, required=True, help='Stock Ticker (e.g. RELIANCE.NS)')
    parser.add_argument('--strategy', type=str, required=True, choices=['RSI', 'EMA', 'BOLLINGER'])
    
    args = parser.parse_args()
    
    generate_report(args.ticker, args.strategy)
