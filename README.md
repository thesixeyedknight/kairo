# Kairo: Algorithmic Trading Simulator

A Python-based event-driven backtester and live paper-trading bot for the Indian Stock Market (NSE).

## Features
- **Engine:** Slippage-aware backtester.
- **Strategies:** Golden RSI, Diamond RSI, Bollinger Squeeze.
- **Modes:** Historical Batch Testing (15m/1H/1D) & Live Paper Trading.

## Quick Start
1. Install dependencies: `conda env create -f environment.yml`
2. Activate: `conda activate kairo_env`
3. Run a test: `python scripts/batch_runner.py --strategy GOLDEN_RSI --interval 1h`