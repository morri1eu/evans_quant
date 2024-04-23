import yfinance as yf

def fetch_data(symbol, start_date, end_date):
    return yf.download(symbol, start=start_date, end=end_date)

