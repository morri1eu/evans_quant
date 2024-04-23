import yfinance as yf
import numpy as np
import pandas as pd

def fetch_individual_stock_data(stock_symbol, start_date='2000-01-01', end_date='2022-01-01'):
    try:
        stock_data = yf.download(stock_symbol, start=start_date, end=end_date)
        if all(column in stock_data.columns for column in ['Close', 'Open', 'High', 'Low', 'Volume']):
            return stock_data
        else:
            print(f"Missing expected columns in the data for {stock_symbol}")
            return None
    except Exception as e:
        print(f"An error occurred while fetching data for {stock_symbol}: {e}")
        return None



def parse_individual_stock_data(stock_data):
     # Calculate VWAP (Volume Weighted Average Price)
    stock_data['VWAP'] = (stock_data['Close'] * stock_data['Volume']).cumsum() / stock_data['Volume'].cumsum()
    
    # Calculate 20-day and 180-day average daily volume
    stock_data['ADV20'] = stock_data['Volume'].rolling(window=20).mean()
    stock_data['ADV180'] = stock_data['Volume'].rolling(window=180).mean()
    
    # Calculate daily returns
    stock_data['Returns'] = stock_data['Close'].pct_change()
    
    # Create a dictionary to hold the NumPy arrays
    data_dict = {
        'close': np.array(stock_data['Close'].dropna()),
        'open_': np.array(stock_data['Open'].dropna()),
        'high': np.array(stock_data['High'].dropna()),
        'low': np.array(stock_data['Low'].dropna()),
        'volume': np.array(stock_data['Volume'].dropna()),
        'vwap': np.array(stock_data['VWAP'].dropna()),
        'adv20': np.array(stock_data['ADV20'].dropna()),
        'adv180': np.array(stock_data['ADV180'].dropna()),
        'returns': np.array(stock_data['Returns'].dropna()),
        'cap': np.array(stock_data['Close'].dropna() * stock_data['Volume'].dropna())  # Simplified market cap
    }
    return data_dict