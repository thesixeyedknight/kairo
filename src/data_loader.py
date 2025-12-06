import os
import time
import pandas as pd
import yfinance as yf

def fetch_data(symbol: str, period='59d', interval='5m') -> pd.DataFrame:
    """
    Fetches financial data for a given symbol.
    Checks for a cached CSV file (modified < 1 hour ago) before hitting the API.
    """
    # Define cache directory and file path
    # Assuming the code is running from project root or scripts folder, 
    # we aim for kairo_project/kairo/data/raw
    # Using relative path assuming execution from project root or adjusting relative to this file
    
    # Ideally, we should detect the project root. 
    # For now, let's assume we can traverse up from this file or use a fixed structure relative to execution.
    # The requirement says "kairo/data/raw/". Let's try to be robust about finding 'kairo'.
    
    # Let's trust the user's structure: kairo/src/data_loader.py
    # kairo/data/raw/ is ../../data/raw relative to this file? No, that would be inside kairo-project/kairo/data
    # This file is in /home/sarthak/kairo_project/kairo/src/data_loader.py
    # So raw data dir is /home/sarthak/kairo_project/kairo/data/raw
    
    current_dir = os.path.dirname(os.path.abspath(__file__)) # kairo/src
    project_kairo_dir = os.path.dirname(current_dir) # kairo
    data_dir = os.path.join(project_kairo_dir, 'data', 'raw')
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    file_path = os.path.join(data_dir, f"{symbol}_{interval}.csv")
    
    # Check if cache exists and is fresh
    if os.path.exists(file_path):
        mtime = os.path.getmtime(file_path)
        if time.time() - mtime < 3600:
            print(f"Loading {symbol} from cache...")
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            return df
            
    print(f"Fetching {symbol} from yfinance...")
    # Fetch data
    df = yf.download(tickers=symbol, period=period, interval=interval, progress=False)
    
    # Keep only required columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    # yfinance multi-index columns handling if necessary (usually single ticker returns simple columns)
    if isinstance(df.columns, pd.MultiIndex):
        df = df.xs(symbol, axis=1, level=1) # This might be needed depending on yf version/structure
        
    # Check if columns are present, sometimes 'Adj Close' is there.
    # If the download failed or is empty
    if df.empty:
        print(f"Warning: No data found for {symbol}")
        return df

    # Filter columns
    df = df[required_cols]
    
    # Drop NaNs
    df.dropna(inplace=True)
    
    # Save to cache
    df.to_csv(file_path)
    
    return df
