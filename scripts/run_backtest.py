import sys
import os
import pandas as pd

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from kairo.src.data_loader import fetch_data
from kairo.src.strategy import RSIStrategy
from kairo.src.backtester import Backtester

def run_backtest():
    # Setup paths
    reports_dir = os.path.join(current_dir, 'reports')
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    report_file = os.path.join(reports_dir, 'backtest_indian_market.md')

    print("Fetching data...")
    # Fetch 59 days of 5m data for RELIANCE.NS
    df = fetch_data('RELIANCE.NS', period='59d', interval='5m')
    
    if df.empty:
        print("Data fetch failed. Exiting.")
        return

    print("Initializing Strategy (RSI)...")
    strategy = RSIStrategy(period=14, buy_threshold=30, sell_threshold=70)

    print("Running Backtest...")
    backtester = Backtester(initial_capital=100000, commission=0.001)
    results = backtester.run(df, strategy)

    # Generate Report
    with open(report_file, 'w') as f:
        f.write("# Backtest Report: RSI Strategy on RELIANCE.NS\n\n")
        
        f.write("## Configuration\n")
        f.write(f"- Symbol: RELIANCE.NS\n")
        f.write(f"- Interval: 5m\n")
        f.write(f"- Strategy: RSI (14, 30, 70)\n")
        f.write(f"- Initial Capital: ₹{results['Initial Capital']}\n\n")
        
        f.write("## Performance Metrics\n")
        f.write("| Metric | Value |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| Final Value | ₹{results['Final Value']:.2f} |\n")
        f.write(f"| ROI | {results['ROI (%)']:.2f}% |\n")
        f.write(f"| Max Drawdown | {results['Max Drawdown (%)']:.2f}% |\n")
        
    print(f"Backtest complete. Results saved to {report_file}")
    print(f"ROI: {results['ROI (%)']:.2f}%")

if __name__ == "__main__":
    run_backtest()
