import json
import os
import pandas as pd
from eod import EodHistoricalData
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()
# Example usage
api_token = os.getenv("EOD_HD_API_KEY")


# Initialize the EOD client
client = EodHistoricalData(api_token)

# Function to fetch and update data


async def fetch_and_update_data(baseline_data_path, exchanges, date):
    # Get the list of exchanges based on existing folders

    # Fetch bulk market data for each exchange
    while not exchanges.empty():
        exchange = await exchanges.get()
        print(exchange)
        bulk_data = client.get_bulk_markets(exchange=exchange, date=date)
        # Update CSV files for each ticker in the bulk data
        for ticker_data in bulk_data:
            print(f"Updating data for {ticker_data['code']} on {exchange}...")
            try:
                # Prepare data for DataFrame
                df_data = {
                    'date': [ticker_data['date']],
                    'open': [ticker_data['open']],
                    'high': [ticker_data['high']],
                    'low': [ticker_data['low']],
                    'close': [ticker_data['close']],
                    'adjusted_close': [ticker_data['adjusted_close']],
                    'volume': [ticker_data['volume']]
                }
                df = pd.DataFrame(df_data)

                csv_file = f'{baseline_data_path}/{exchange}/{ticker_data["code"]+"_baseline"}.csv'

                # If CSV exists, update it. Otherwise, create a new one.
                if os.path.exists(csv_file):

                    try:
                        existing_df = pd.read_csv(csv_file)
                        updated_df = pd.concat(
                            [existing_df, df]).drop_duplicates()
                        updated_df.to_csv(csv_file, index=False)
                        print(
                            f"Data for {ticker_data['code']}, on exchange {exchange}, updated in {csv_file}")
                    except Exception as e:
                        print(
                            f"An error occurred while updating data for {ticker_data['code']}: {e}")
                        continue
                else:
                    print('does not exist')

            except Exception as e:
                print(
                    f"An error occurred while updating data for {ticker_data['code']}: {e}")
                continue


async def main(baseline_data_path, date):
    print('main')
    exchanges = [name for name in os.listdir(baseline_data_path) if os.path.isdir(
        os.path.join(baseline_data_path, name))]
    print(exchanges)
    work_queue = asyncio.Queue()
    for exchange in exchanges:
        await work_queue.put(exchange)
        await work_queue.put(exchange)
    await asyncio.gather(
        asyncio.create_task(fetch_and_update_data(
            baseline_data_path, work_queue, date)),
    )
