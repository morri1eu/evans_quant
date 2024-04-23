import pandas as pd
import numpy as np


def calculate_rsi(data, window=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def backtest_rsi_strategy(data, rsi_entry_threshold=30, rsi_exit_threshold=70, stop_loss_pct=0.05, take_profit_pct=0.01):
    data['rsi'] = calculate_rsi(data, 3)
    data['position'] = 0
    in_position = False
    entry_price = 0

    # Calculate average holding period
    entry_point = []
    exit_point = []
    for i in range(1, len(data)):
        if not in_position and data['rsi'].iloc[i] < rsi_entry_threshold:
            data.at[i, 'position'] = 1  # Buy
            in_position = True
            entry_price = data['close'].iloc[i]
            entry_point.append(i)
        elif in_position:
            current_price = data['close'].iloc[i]
            stop_loss = entry_price * (1 - stop_loss_pct)
            take_profit = entry_price * (1 + take_profit_pct)

            if current_price <= stop_loss or current_price >= take_profit or data['rsi'].iloc[i] > rsi_exit_threshold:
                data.at[i, 'position'] = -1  # Sell
                in_position = False
                exit_point.append(i)

    data['daily_return'] = data['close'].pct_change()
    data['strategy_return'] = data['daily_return'] * data['position'].shift(1)

    # Calculate average holding period
    holding_periods = []
    for i in range(len(entry_point)):
        if i < len(exit_point):
            holding_periods.append(exit_point[i] - entry_point[i])
    avg_holding_period = np.mean(holding_periods)
    max_holding_period = np.max(holding_periods)
    median_holding_period = np.median(holding_periods)
    print(f'Maximum holding period: {max_holding_period} minutes')
    print(f'Median holding period: {median_holding_period} minutes')
    print(f'Average holding period: {avg_holding_period} minutes')
    return data


def evaluate_performance(data):

    total_return = data['strategy_return'].cumsum().iloc[-1]
    sharpe_ratio = np.sqrt(252 * 60) * (data['strategy_return'].mean(
    ) / data['strategy_return'].std())  # Adjusted for minute data
    drawdown = (data['strategy_return'].cummax() -
                data['strategy_return']).max()
    # handle average holding periods

    return total_return, sharpe_ratio, drawdown


# # Load data
# data = pd.read_csv('path_to_your_csv_file.csv', parse_dates=['datetime'])

# # Backtest the strategy
# backtested_data = backtest_rsi_strategy(data)

# # Evaluate performance
# total_return, sharpe_ratio, drawdown = evaluate_performance(backtested_data)

# print(f'Total Return: {total_return}')
# print(f'Sharpe Ratio: {sharpe_ratio}')
# print(f'Maximum Drawdown: {drawdown}')
