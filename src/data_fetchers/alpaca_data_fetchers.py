from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# No keys required for crypto data

def get_stock_client():
    return StockHistoricalDataClient()

def get_crypto_client():
    return CryptoHistoricalDataClient()

def create_crypto_bars_request_params(symbols, timeframe, start, end):
    return CryptoBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=timeframe,
        start=start,
        end=end
    )

def fetch_crypto_bars_request(symbol, timeframe, start, end):
    try: 
      client = get_crypto_client()
      request_params = create_crypto_bars_request_params(symbol, timeframe, start, end)
      return client.get_crypto_bars(request_params).df
    except Exception as e:
      print(f"An error occurred while fetching data for {symbol}: {e}")
      return None

def create_stock_bars_request_params(symbols, timeframe, start, end):
    return StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=timeframe,
        start=start,
        end=end
    )

def fetch_stock_bars_request(symbol, timeframe, start, end):
    try: 
      client = get_stock_client()
      request_params = create_stock_bars_request_params(symbol, timeframe, start, end)
      return client.get_stock_bars(request_params).df
    except Exception as e:
      print(f"An error occurred while fetching data for {symbol}: {e}")
      return None