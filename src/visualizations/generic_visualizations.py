# visualizations/generic_visualization.py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os


def plot_strategy(data, portfolio, strategy_name='Strategy'):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9))

    ax1.plot(data['close'], label='Price')
    ax1.plot(data['VWAP'], label='VWAP')
    ax1.set_title(f'{strategy_name}')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price')
    ax1.legend()

    ax2.plot(portfolio['Total'], label='Portfolio Value')
    ax2.set_title('Portfolio Value Over Time')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Portfolio Value in $')
    ax2.legend()

    plt.tight_layout()
    plt.show()


def calculate_atr(data, period=14):
    print('calculating atr with data', data)
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    true_ranges = np.maximum(high_low, high_close, low_close)
    atr = true_ranges.rolling(window=period).mean()
    return atr


def calculate_rsi(data, period=14):
    delta = data['close'].diff()
    up_days = delta.copy()
    up_days[delta <= 0] = 0.0
    down_days = abs(delta.copy())
    down_days[delta > 0] = 0.0
    RS_up = up_days.rolling(window=period).mean()
    RS_down = down_days.rolling(window=period).mean()
    rsi = 100-100/(1+RS_up/RS_down)
    return rsi


def get_indicators_for_stock(stock_ticker, exchange=None, should_print=False, should_save_csv=False):
    try:
        # read data from csv
        if exchange:
            path = f'../data/baseline_data/{exchange}/{stock_ticker}_baseline.csv'
            data = pd.read_csv(path)
        else:
            path = f'../data/tick_data/{stock_ticker}.csv'
            data = pd.read_csv(path)

        # calculate metrics & indicators

        # RSI (Relative Strength Index)
        rsi_21 = calculate_rsi(data, 21)
        rsi_14 = calculate_rsi(data)
        rsi_7 = calculate_rsi(data, 7)

        # SMA (Simple Moving Average)
        sma_20 = data['close'].rolling(window=20).mean()
        sma_50 = data['close'].rolling(window=50).mean()
        sma_200 = data['close'].rolling(window=200).mean()

        data['rsi_21'] = rsi_21
        data['rsi_14'] = rsi_14
        data['rsi_7'] = rsi_7
        data['sma_20'] = sma_20
        data['sma_50'] = sma_50
        data['sma_200'] = sma_200
        # return data
        if should_print:
            if exchange:
                plot_data_with_indicators(data.tail(30), stock_ticker)
            else:
                plot_data_with_indicators_interval(data.tail(30), stock_ticker)
            if should_save_csv:
                data.to_csv(
                    f'../data/tick_data/{stock_ticker}.csv', index=False)
        return data
    except:
        print(f'Error getting data for {stock_ticker}')
        return pd.DataFrame()


def plot_data_with_indicators(data, stock_ticker):
    fig, ax1 = plt.subplots(figsize=(16, 9))

    # Plotting Price and SMAs on the primary y-axis
    ax1.plot(data['date'], data['close'], label='Price', color='blue')
    ax1.plot(data['date'], data['sma_20'], label='SMA 20', color='orange')
    ax1.plot(data['date'], data['sma_50'], label='SMA 50', color='green')
    ax1.set_title(f'{stock_ticker} Price and Indicators')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price/SMA')
    ax1.legend(loc='upper left')

    # Creating a secondary y-axis for RSI
    ax2 = ax1.twinx()
    ax2.plot(data['date'], data['rsi_21'], label='RSI 21',
             color='red', linestyle='dashed')
    ax2.plot(data['date'], data['rsi_14'], label='RSI 14',
             color='purple', linestyle='dashed')
    ax2.plot(data['date'], data['rsi_7'], label='RSI 7',
             color='pink', linestyle='dashed')
    ax2.set_ylabel('RSI')
    ax2.legend(loc='upper right')

    plt.tight_layout()
    plt.show()


def plot_data_with_indicators_interval(data, stock_ticker):
    fig, ax1 = plt.subplots(figsize=(16, 9))

    # Plotting Price and SMAs on the primary y-axis
    ax1.plot(data['timestamp'], data['close'], label='Price', color='blue')
    ax1.plot(data['timestamp'], data['sma_20'],
             label='SMA 20', color='orange')
    ax1.plot(data['timestamp'], data['sma_50'],
             label='SMA 50', color='green')
    ax1.set_title(f'{stock_ticker} Price and Indicators')
    ax1.set_xlabel('timestamp')
    ax1.set_ylabel('Price/SMA')
    ax1.legend(loc='upper left')

    # Creating a secondary y-axis for RSI
    ax2 = ax1.twinx()
    ax2.plot(data['timestamp'], data['rsi_21'], label='RSI 21',
             color='red', linestyle='dashed')
    ax2.plot(data['timestamp'], data['rsi_14'], label='RSI 14',
             color='purple', linestyle='dashed')
    ax2.plot(data['timestamp'], data['rsi_7'], label='RSI 7',
             color='pink', linestyle='dashed')
    ax2.set_ylabel('RSI')
    ax2.legend(loc='upper right')

    plt.tight_layout()
    plt.show()


def calculate_and_print_metrics(portfolio, stock_ticker, should_print, data):
    returns = portfolio['Returns'].dropna()
    volatility = returns.std()
    sharpe_ratio = np.sqrt(252) * returns.mean() / volatility if volatility != 0 else np.nan

    portfolio['Peak'] = portfolio['Total'].cummax()
    portfolio['Drawdown'] = (portfolio['Total'] - portfolio['Peak']) / portfolio['Peak']
    max_drawdown = portfolio['Drawdown'].min()

    drawdown_duration = (portfolio['Drawdown'] == 0).astype(int)
    drawdown_duration = drawdown_duration.groupby(
        (drawdown_duration != drawdown_duration.shift()).cumsum()).cumsum()
    max_drawdown_duration = drawdown_duration.max()

    annualized_return = (1 + returns.mean()) ** 252 - 1 if not returns.empty else np.nan
    total_return = portfolio['Total'].iloc[-1] / portfolio['Total'].iloc[0] - 1 if len(portfolio['Total']) else np.nan

    average_true_range = calculate_atr(data)

    rsi_21 = calculate_rsi(data, 21)
    rsi_14 = calculate_rsi(data)
    rsi_7 = calculate_rsi(data, 7)

    sma_20 = data['close'].rolling(window=20).mean()
    sma_50 = data['close'].rolling(window=50).mean()
    sma_200 = data['close'].rolling(window=200).mean()

    if should_print:
        print(f'Portfolio Metrics: {stock_ticker}')
        print(f'Sharpe Ratio: {sharpe_ratio}')
        print(f'Maximum Drawdown: {max_drawdown}')
        print(f'Maximum Drawdown Duration: {max_drawdown_duration} days')
        print(f'Annualized Return: {annualized_return}')
        print(f'Total Return: {total_return}')

    return [stock_ticker, sharpe_ratio, max_drawdown, max_drawdown_duration, annualized_return, total_return, average_true_range, rsi_21, rsi_14, rsi_7, sma_20, sma_50, sma_200]


def create_csv_from_metrics(exchange, alpha_name, df):
    # Create dataframe from metrics
    directory = f'../data/backtest_results/{exchange}'
    if not os.path.exists(directory):
        os.makedirs(directory)

    path = f'../data/backtest_results/{exchange}/{alpha_name}_metrics.csv'
    df.to_csv(path, index=False)


def create_df_from_metrics(exchange_stock_data, bound):
    df = pd.DataFrame(columns=['Stock', 'Sharpe Ratio', 'Max Drawdown', 'Max Drawdown Duration',
                      'Annualized Return', 'Total Return', 'Average True Range', 'Bound'])
    for stock_data in exchange_stock_data:
        stock_ticker = stock_data[0]
        sharpe_ratio = stock_data[1]
        max_drawdown = stock_data[2]
        max_drawdown_duration = stock_data[3]
        annualized_return = stock_data[4]
        total_return = stock_data[5]
        average_true_range = stock_data[6]
        df.loc[len(df)] = [stock_ticker, sharpe_ratio, max_drawdown, max_drawdown_duration,
                           annualized_return, total_return, average_true_range, bound]
    return df


def calculate_mean_sharpe_ratio_from_metrics(exchange_stock_data, bound):
    df = create_df_from_metrics(exchange_stock_data, bound)
    return df['Sharpe Ratio'].mean()
