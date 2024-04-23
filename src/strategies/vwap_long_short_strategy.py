import pandas as pd
import numpy as np
from src.strategies.portfolio import initialize_portfolio
from src.visualizations.generic_visualizations import plot_strategy
import matplotlib.pyplot as plt
import datetime


def calculate_vwap(data):
    data['TP'] = (data['high'] + data['low'] + data['close']) / 3
    data['TPV'] = data['TP'] * data['volume']
    # data['cumulative_TPV'] = data['TPV'].cumsum()
    # data['cumulative_volume'] = data['volume'].cumsum()
    data['VWAP'] = data['TPV'] / data['volume']
    return data


def vwap_long_short_strategy(data):
    # Calculate VWAP
    data_with_vwap = calculate_vwap(data)

    # Initialize portfolio
    portfolio = initialize_portfolio(
        data_with_vwap)
    in_long_position = False
    in_short_position = False
    entry_date_time = None
    current_day = None
    # Implement strategy long when vwap > close and short when vwap < close once in position hold until vwap crosses close
    for i in range(1, len(data_with_vwap)):
        current_date_time = pd.to_datetime(
            data_with_vwap.iloc[i]['datetime'])
        # print('current datetime', current_date_time)
        # if current_date_time.day != current_day:
        #     current_day = current_date_time.day
        #     in_long_position = False
        #     in_short_position = False
        #     entry_date_time = None

        current_bar = data_with_vwap.iloc[i]
        is_market_open = get_is_market_open(current_bar['datetime'])
        is_market_closing = get_is_market_closing(
            current_bar['datetime'])
        current_close = current_bar['close']
        if is_market_open:
            current_long_signal = get_long_signal(current_bar)
            current_short_signal = get_short_signal(current_bar)
            if entry_date_time is None:
                if current_long_signal:
                    entry_date_time = current_bar['datetime']
                    in_long_position = True
                    minute_return = 0
                elif current_short_signal:
                    entry_date_time = current_bar['datetime']
                    in_short_position = True
                    minute_return = 0

            entry_price = entry_date_time and data_with_vwap.where(
                data_with_vwap['datetime'] == entry_date_time)['close'].dropna().iloc[0]
            # Check if market is closing
            if is_market_closing:
                if in_long_position:

                    minute_return = (current_close / entry_price) - 1
                    in_long_position = False
                    # print('long position closed at close', minute_return)
                elif in_short_position:
                    minute_return = (entry_price / current_close) - 1
                    in_short_position = False
                    # print('short position closed at close', minute_return)
                else:
                    minute_return = 0

            if in_long_position:
                if current_short_signal:
                    minute_return = current_close / \
                        entry_price - 1
                    in_long_position = False
                    # print('long position closed at short signal', minute_return)
                else:
                    minute_return = 0

            elif in_short_position:
                if current_long_signal:
                    minute_return = entry_price / \
                        current_close - 1
                    in_short_position = False
                    # print('short position closed at long signal', minute_return)
                else:
                    minute_return = 0
            else:
                if current_long_signal:
                    entry_date_time = current_bar['datetime']
                    in_long_position = True
                    minute_return = 0
                elif current_short_signal:
                    entry_date_time = current_bar['datetime']
                    in_short_position = True
                    minute_return = 0
                else:
                    minute_return = 0
        else:  # Market is closed
            minute_return = 0
        # Update portfolio
        portfolio.at[i, 'Returns'] = minute_return
        # print(portfolio.at[i, 'Returns'])
        portfolio.at[i, 'Total'] = portfolio.at[i -
                                                1, 'Total'] * (1 + minute_return)
    plot_strategy(data_with_vwap, portfolio,
                  strategy_name='VWAP Long Short Strategy')
    return portfolio


def get_long_signal(current_minute_bar):
    if current_minute_bar['VWAP'] is None:
        return False
    if current_minute_bar['close'] > current_minute_bar["VWAP"]:
        return True
    return False


def get_short_signal(current_minute_bar):
    if current_minute_bar['VWAP'] is None:
        return False
    if current_minute_bar['close'] < current_minute_bar["VWAP"]:
        return True
    return False


def get_is_market_open(datetime):
    time_as_datetime = pd.to_datetime(datetime)
    is_after_open = time_as_datetime.hour >= 13 and time_as_datetime.minute > 30 or time_as_datetime.hour > 13
    is_before_close = time_as_datetime.hour < 21
    is_weekday = time_as_datetime.weekday() < 5
    if is_weekday and is_after_open and is_before_close:
        return True
    return False


def get_is_market_closing(datetime):
    time_as_datetime = pd.to_datetime(datetime)
    if time_as_datetime.weekday() < 5 and time_as_datetime.hour == 20 and time_as_datetime.minute == 59:
        return True
    return False
