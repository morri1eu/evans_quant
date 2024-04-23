import pandas as pd

def calculate_metrics(df):
    # Calculate daily close-to-close returns
    df['returns'] = df['close'].pct_change()
    
    # Calculate VWAP (Volume Weighted Average Price)
    df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
    
    # Calculate market cap (Here, I'm assuming you have a 'shares_outstanding' column. If not, you'll need to fetch this data.)
    # df['cap'] = df['close'] * df['shares_outstanding']
    
    # Calculate ADV (Average Daily Dollar Volume) for past d days. Here, I'm using d=20 as an example.
    df['adv20'] = df['volume'] * df['vwap']
    df['adv20'] = df['adv20'].rolling(window=20).mean()
    
    # Calculate ADV for other periods (e.g., d=50, d=100)
    df['adv50'] = df['volume'] * df['vwap']
    df['adv50'] = df['adv50'].rolling(window=50).mean()
    
    df['adv100'] = df['volume'] * df['vwap']
    df['adv100'] = df['adv100'].rolling(window=100).mean()
    
    return df

def calculate_signals(df):
    # Calculate the 20-day and 100-day simple moving averages
    df['SMA20'] = df['close'].rolling(window=20).mean()
    df['SMA100'] = df['close'].rolling(window=100).mean()
    
    # Calculate the 20-day and 100-day exponential moving averages
    df['EMA20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA100'] = df['close'].ewm(span=100, adjust=False).mean()
    
    # Calculate the MACD
    df['MACD'] = df['EMA20'] - df['EMA100']
    
    # Calculate the RSI
    delta = df['close'].diff()
    up_days = delta.copy()
    up_days[delta <= 0] = 0.0
    down_days = abs(delta.copy())
    down_days[delta > 0] = 0.0
    RS_up = up_days.rolling(window=14).mean()
    RS_down = down_days.rolling(window=14).mean()
    df['RSI'] = 100.0 - (100.0 / (1.0 + RS_up / RS_down))
    
    # Calculate the ATR
    df['ATR'] = df['high'] - df['low']
    df['ATR'] = df['ATR'].ewm(span=14, adjust=False).mean()
    
    # Calculate the Bollinger Bands
    df['BB_upper'] = df['SMA20'] + 2 * df['close'].rolling(window=20).std(ddof=0)
    df['BB_lower'] = df['SMA20'] - 2 * df['close'].rolling(window=20).std(ddof=0)

    return df

def calculate_positions(df):
    # Calculate the daily market return
    df['market_return'] = df['close'].pct_change()
    
    # Calculate the daily strategy return
    df['strategy_return'] = df['market_return'] * df['position']
    
    # Calculate the cumulative strategy returns
    df['cumulative_strategy_return'] = (df['strategy_return'] + 1).cumprod()
    
    return df

def extract_close_from_df(df):
    return df['close'].dropna()

def extract_last_close_from_df(df):
    return df['close'].dropna().iloc[-1]

def extract_open_from_df(df):
    return df['open'].dropna()

def extract_last_open_from_df(df):
    return df['open'].dropna().iloc[-1]

def extract_volume_from_df(df):
    return df['volume'].dropna()

def extract_last_volume_from_df(df):
    return df['volume'].dropna().iloc[-1]

def extract_returns_from_df(df):
    return df['returns'].dropna()

def extract_vwap_from_df(df):
    return df['vwap'].dropna()

def extract_adv20_from_df(df):
    return df['adv20'].dropna()

def extract_adv50_from_df(df):
    return df['adv50'].dropna()

def extract_adv100_from_df(df):
    return df['adv100'].dropna()

def extract_sma20_from_df(df):
    return df['SMA20'].dropna()

def extract_sma100_from_df(df):
    return df['SMA100'].dropna()

def extract_ema20_from_df(df):
    return df['EMA20'].dropna()

def extract_ema100_from_df(df):
    return df['EMA100'].dropna()

def extract_macd_from_df(df):
    return df['MACD'].dropna()

def extract_rsi_from_df(df):
    return df['RSI'].dropna()

def extract_atr_from_df(df):
    return df['ATR'].dropna()

def extract_bb_upper_from_df(df):
    return df['BB_upper'].dropna()

def extract_bb_lower_from_df(df):
    return df['BB_lower'].dropna()

