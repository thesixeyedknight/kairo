import sys
import os
import shutil

# Add project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from kairo.src.paper_broker import PaperBroker

def test_broker():
    print("Testing Paper Broker Persistence...")
    
    # 1. Setup Test Env (Clear old data)
    data_dir = os.path.join(project_root, 'data')
    json_path = os.path.join(data_dir, 'paper_portfolio.json')
    if os.path.exists(json_path):
        os.remove(json_path)
        print("Cleared old portfolio data.")
        
    # 2. Init Broker (Check Default)
    broker = PaperBroker()
    cash = broker.get_balance()
    print(f"Initial Cash: {cash}")
    assert cash == 10000.0, f"Expected 10000, got {cash}"
    
    # 3. Execute BUY
    # Buy 'TEST.NS' at 100.
    # Commission 0.15% = 0.15 per share. Cost basis ~100.15.
    # Max shares = 10000 / 100.15 ~= 99
    broker.execute_trade('TEST.NS', 1, 100.0)
    
    qty = broker.get_position('TEST.NS')
    new_cash = broker.get_balance()
    print(f"Post-Buy | Qty: {qty} | Cash: {new_cash:.2f}")
    assert qty > 0, "Trade failed to executed buy"
    assert new_cash < 10000, "Cash didn't decrease"
    
    # 4. Verify Persistence (Reload)
    print("Reloading Broker from disk...")
    broker2 = PaperBroker()
    loaded_qty = broker2.get_position('TEST.NS')
    assert loaded_qty == qty, f"Persistence Fail: Expected {qty}, got {loaded_qty}"
    print("Persistence Check Passed.")
    
    # 5. Execute SELL (Profit)
    # Sell at 110. Profit = (110 - 100) * qty - comms.
    broker2.execute_trade('TEST.NS', -1, 110.0)
    
    final_cash = broker2.get_balance()
    final_qty = broker2.get_position('TEST.NS')
    print(f"Post-Sell | Qty: {final_qty} | Cash: {final_cash:.2f}")
    
    assert final_qty == 0, "Sell failed to clear position"
    assert final_cash > 10000, "Expected profit but cash is lower/equal"
    
    print("Broker Test Completed Successfully.")

if __name__ == "__main__":
    test_broker()
