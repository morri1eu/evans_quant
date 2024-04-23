import json
import os
import pandas as pd
from eod import EodHistoricalData
import asyncio
import json
from dotenv import load_dotenv
import os

load_dotenv()
# Example usage
api_token = os.getenv("EOD_HD_API_KEY")

# Initialize the EOD client
client = EodHistoricalData(api_token)

# Function to fetch and update data


async def fetch_and_update_tick_data(tick_data_output_path, stock_universe, interval='1m'):
    # Get the list of stock_universe based on existing folders

    # Fetch bulk market data for each stock
    while not stock_universe.empty():
        stock = await stock_universe.get()
        print(stock)
        bulk_data = client.get_prices_intraday(
            f'{stock}.US', interval=interval, fmt='csv',)
        # Update CSV files for each ticker in the bulk data
        pd.DataFrame(bulk_data).to_csv(
            f'{tick_data_output_path}/{stock}{interval}.csv', index=False)


async def fetch_tick_data(tick_data_output_path, stock, interval='1m'):
    stock_data = client.get_prices_intraday(
        f'{stock}.US', interval=interval, fmt='csv',)
    # Update CSV files for each ticker in the bulk data
    return pd.DataFrame(stock_data)


async def main(tick_data_output_path, from_to, interval='1m'):
    print('main')
    with open('../data/tick_data/universe/small_stock_name.json', 'r') as file:
        stock_universe = json.load(file)
    stock_universe = [
        'TQQQ',
        # 'DKNG',
        # 'FUBO',
        # 'LULU',
        # 'AFRM',
        # 'RBLX',
        # 'COIN',
        # 'CVNA',
        # 'ABNB',
        # 'FSLY',
        # 'BYND',
        # 'DDOG'
    ]
    print(stock_universe)
    work_queue = asyncio.Queue()
    for stock in stock_universe:
        await work_queue.put(stock)

    await asyncio.gather(
        asyncio.create_task(fetch_and_update_tick_data(
            tick_data_output_path, work_queue, from_to, interval)),
    )
