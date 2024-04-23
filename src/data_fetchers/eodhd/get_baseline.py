import json
import os
import pandas as pd
from datetime import datetime, timedelta
from eodhd import APIClient

def fetch_baseline_data(api_token, tickers_json_path, output_folder):
    # Initialize the EODHD client
    eodhd_client = APIClient(api_token)
    
    print("Fetching baseline data...")
    # Read tickers from the JSON file
    with open(tickers_json_path, 'r') as f:
        tickers_data = json.load(f)
    
    # Group tickers by exchange
    tickers_by_exchange = {}
    for ticker_data in tickers_data:
        exchange = ticker_data['Exchange']
        code = ticker_data['Code']
        if exchange not in tickers_by_exchange:
            tickers_by_exchange[exchange] = []
        tickers_by_exchange[exchange].append(code)
    
    print(tickers_by_exchange)
    # Calculate the date 2 years ago from today
    two_years_ago = (datetime.now() - timedelta(days=910)).strftime('%Y-%m-%d')
    print(two_years_ago)
    # Fetch and save data for each ticker, grouped by exchange
    for exchange, tickers in tickers_by_exchange.items():
        print('exchange', exchange)
        exchange_folder = os.path.join(output_folder, exchange)
        os.makedirs(exchange_folder, exist_ok=True)
        
        for ticker in tickers:
            print(f"Fetching data for {ticker} on {exchange}...")
            
            # Fetch data for the past 2 years
            data = eodhd_client.get_eod_historical_stock_market_data(ticker, from_date=two_years_ago)

            # Save to a CSV file
            output_file_path = os.path.join(exchange_folder, f"{ticker}_baseline.csv")
            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Write to CSV
            df.to_csv(output_file_path, index=False)
            print(f"Data for {ticker} saved in {output_file_path}")


