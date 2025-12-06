import json
import os
from datetime import datetime

class PaperBroker:
    def __init__(self, data_dir=None):
        if data_dir is None:
            # Default to project volume
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.data_dir = os.path.join(base_dir, 'data')
        else:
            self.data_dir = data_dir
            
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self.portfolio_file = os.path.join(self.data_dir, 'paper_portfolio.json')
        self.state = self._load_state()
        self.commission_rate = 0.0015 # 0.15%

    def _load_state(self):
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error reading {self.portfolio_file}, resetting to default.")
        
        # Default State
        return {
            "cash": 10000.0,
            "positions": {},
            "trade_log": []
        }

    def _save_state(self):
        with open(self.portfolio_file, 'w') as f:
            json.dump(self.state, f, indent=4)

    def get_balance(self):
        return self.state['cash']

    def get_position(self, ticker):
        """Returns number of shares held for a ticker."""
        return self.state['positions'].get(ticker, 0)

    def execute_trade(self, ticker, signal, price, date_str=None):
        """
        Executes a trade based on signal.
        Signal 1: Buy (Uses all cash)
        Signal -1: Sell (Closes position)
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if signal == 1:
            # BUY Logic
            cash = self.state['cash']
            # We need to account for commission in max shares
            # Cost = Shares * Price
            # Comm = Shares * Price * Rate
            # Total = Shares * Price * (1 + Rate) <= Cash
            max_shares = int(cash / (price * (1 + self.commission_rate)))
            
            if max_shares > 0:
                cost = max_shares * price
                commission = cost * self.commission_rate
                total_cost = cost + commission
                
                self.state['cash'] -= total_cost
                current_qty = self.state['positions'].get(ticker, 0)
                self.state['positions'][ticker] = current_qty + max_shares
                
                trade_record = {
                    "date": date_str,
                    "ticker": ticker,
                    "action": "BUY",
                    "price": price,
                    "shares": max_shares,
                    "value": cost,
                    "commission": commission,
                    "remaining_cash": self.state['cash']
                }
                self.state['trade_log'].append(trade_record)
                self._save_state()
                print(f"[PAPER] BOUGHT {max_shares} {ticker} @ {price:.2f}")
                return True
            else:
                print(f"[PAPER] INSUFFICIENT CASH for {ticker}")
                return False

        elif signal == -1:
            # SELL Logic
            shares = self.state['positions'].get(ticker, 0)
            
            if shares > 0:
                value = shares * price
                commission = value * self.commission_rate
                net_proceeds = value - commission
                
                self.state['cash'] += net_proceeds
                # Assuming full exit
                del self.state['positions'][ticker]
                
                trade_record = {
                    "date": date_str,
                    "ticker": ticker,
                    "action": "SELL",
                    "price": price,
                    "shares": shares,
                    "value": value,
                    "commission": commission,
                    "remaining_cash": self.state['cash']
                }
                self.state['trade_log'].append(trade_record)
                self._save_state()
                print(f"[PAPER] SOLD {shares} {ticker} @ {price:.2f}")
                return True
            else:
                # No position to sell
                return False
        
        return False
