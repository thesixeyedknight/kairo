import sys
import os
import pandas as pd

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from kairo.src.data_loader import fetch_data
from kairo.src.strategy import GoldenRSIStrategy
from kairo.src.backtester import Backtester

# Try to import tabulate
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

def optimize_params(ticker='BPCL.NS'):
    print(f"Starting Parameter Optimization for {ticker}")
    print("-" * 50)

    # Configuration
    INTERVAL = '1h'
    PERIOD = '700d'
    
    # Parameter Grid
    RSI_PERIODS = [7, 10, 14, 21]
    EMA_FILTERS = [50, 100, 200]
    
    # Fetch Data Once
    print(f"Fetching data for {ticker} ({PERIOD}, {INTERVAL})...")
    df = fetch_data(ticker, period=PERIOD, interval=INTERVAL)
    
    if df.empty:
        print("No data found.")
        return

    results = []
    
    backtester = Backtester(initial_capital=10000, commission=0.0015)
    
    total_combinations = len(RSI_PERIODS) * len(EMA_FILTERS)
    count = 0
    
    print(f"Testing {total_combinations} combinations...")
    
    for rsi in RSI_PERIODS:
        for ema in EMA_FILTERS:
            count += 1
            # Instantiate Strategy with params
            # Note: keeping default stop/take profit for now, optimizing core indicators
            strategy = GoldenRSIStrategy(rsi_period=rsi, ema_filter=ema)
            
            # Run Backtest
            metrics = backtester.run(df, strategy)
            
            # Calculate Win Rate
            trades = metrics['Trades']
            win_count = 0
            for t in trades:
                # Need to find profit/loss per trade. 
                # Backtester trades list splits Buy and Sell.
                # A "trade" usually implies a round trip.
                # Simplified: Current backtester trades list has separate Buy and Sell events.
                # We can't easily calculate win rate without matching them.
                # However, our Backtester doesn't explicitly link them in the list.
                # It just calculates final equity.
                pass
            
            # Let's derive Win Rate roughly or skip it?
            # User asked for "ROI, Win Rate, Trades".
            # To get Win Rate properly, we'd need to match Buys and Sells.
            # Since 'Sell' event has 'Value' (Revenue) and corresponding 'Buy' had 'Value' (Cost).
            # But position sizing changes.
            # Given current Backtester structure (fifo/lifo not explicit, just cash/shares tracking),
            # Precise PnL per trade is hard without refactoring backtester.
            
            # HACK: Let's iterate trades list. 
            # Assumes 1 Buy followed by 1 Sell (simplest case for this strategy usually).
            # If multiple buys, it gets complex.
            # For now, let's report "Trade Count" (Executions / 2 approx).
            
            # Actually, `metrics['Trades']` contains all executions.
            # Let's pair them up if possible.
            # Or just report ROI and Trade Count (Executions).
            # "Win Rate" might be skipped or estimated.
            
            # Let's try to estimate PnL from sequential Buy/Sell pairs
            # This is brittle but better than nothing.
            
            pnl_list = []
            open_position = None
            
            for t in trades:
                if t['Type'] == 'Buy':
                    open_position = t
                elif 'Sell' in t['Type'] and open_position:
                    # Closing
                    cost = open_position['Value'] + open_position['Commission']
                    revenue = t['Value'] - t['Commission']
                    profit = revenue - cost
                    pnl_list.append(profit)
                    open_position = None
            
            wins = len([p for p in pnl_list if p > 0])
            total_closed_trades = len(pnl_list)
            win_rate = (wins / total_closed_trades * 100) if total_closed_trades > 0 else 0.0
            
            results.append({
                'RSI': rsi,
                'EMA': ema,
                'ROI (%)': metrics['ROI (%)'],
                'Max DD (%)': metrics['Max Drawdown (%)'],
                'Trades': total_closed_trades,
                'Win Rate (%)': win_rate
            })
            
            # Simple progress
            # print(f"[{count}/{total_combinations}] RSI={rsi}, EMA={ema} -> ROI={metrics['ROI (%)']:.2f}%")

    # Create DataFrame
    results_df = pd.DataFrame(results)
    
    # Sort by ROI
    results_df = results_df.sort_values(by='ROI (%)', ascending=False)
    
    print("\noptimization Results:")
    if HAS_TABULATE:
        print(tabulate(results_df, headers='keys', tablefmt='psql', showindex=False))
    else:
        print(results_df.to_string(index=False))
        
    best = results_df.iloc[0]
    print("\n" + "="*30)
    print(f"BEST PARAMETERS for {ticker}")
    print(f"RSI Period : {int(best['RSI'])}")
    print(f"EMA Filter : {int(best['EMA'])}")
    print(f"Result     : ROI {best['ROI (%)']:.2f}% | WR {best['Win Rate (%)']:.1f}%")
    print("="*30 + "\n")

if __name__ == "__main__":
    target = 'BPCL.NS'
    if len(sys.argv) > 1:
        target = sys.argv[1]
    optimize_params(target)
