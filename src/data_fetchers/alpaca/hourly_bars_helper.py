from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest, StockBarsRequest, StockLatestBarRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
import datetime
import os
from dotenv import load_dotenv
import polars as pl
import pandas as pd
from alpaca.data.enums import DataFeed


def get_stock_client():
    env = load_dotenv()
    ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
    ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
    return StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)


def create_stock_bars_request_params(symbols, timeframe, start):
    return StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=timeframe,
        start=start,

    )


def fetch_hourly_stock_bars_for_rsi_divergence_start_up(symbol):

    client = get_stock_client()
    timeframe = TimeFrame(30, TimeFrameUnit.Minute)
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=30)
    request_params = create_stock_bars_request_params(
        symbol, timeframe, start_date)
    stock_return = client.get_stock_bars(request_params)
    df = stock_return.df
    data = df.reset_index()
    data['datetime'] = pd.to_datetime(data['timestamp'])
    data.set_index('datetime', inplace=True)
    data.drop(columns=['timestamp'], inplace=True)
    start_time = pd.Timestamp('14:30').time()
    end_time = pd.Timestamp('21:00').time()
    data = data[data.index.dayofweek < 5]
    data = data[data.index.time >= start_time]
    data = data[data.index.time <= end_time]
    return data


def fetch_minute_stock_bars_for_rsi_divergence_start_up(symbol):

    client = get_stock_client()
    timeframe = TimeFrame(1, TimeFrameUnit.Minute)
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=2)
    request_params = create_stock_bars_request_params(
        symbol, timeframe, start_date)
    stock_return = client.get_stock_bars(request_params)
    df = stock_return.df
    print('df last rows date time', df.tail(1))
    data = df.reset_index()
    data['datetime'] = pd.to_datetime(data['timestamp'])
    data.set_index('datetime', inplace=True)
    data.drop(columns=['timestamp'], inplace=True)
    start_time = pd.Timestamp('14:30').time()
    end_time = pd.Timestamp('21:00').time()
    data = data[data.index.dayofweek < 5]
    data = data[data.index.time >= start_time]
    data = data[data.index.time <= end_time]

    return pl.from_pandas(data)


def fetch_latest_30min_bar(symbol):
    client = get_stock_client()
    timeframe = TimeFrame(30, TimeFrameUnit.Minute)
    request_params = StockLatestBarRequest(
        symbol_or_symbols=symbol,
        timeframe=timeframe,
        feed=DataFeed.SIP
    )
    data = client.get_stock_latest_bar(request_params)
    print('data', data)
    data = data[symbol]
    row_to_append = {
        'open': data.open,
        'high': data.high,
        'low': data.low,
        'close': data.close,
        'volume': data.volume,
        'datetime': pd.to_datetime(data.timestamp),
        'trade_count': data.trade_count,
        'vwap': data.vwap,
        'symbol': symbol,
    }
    return row_to_append
