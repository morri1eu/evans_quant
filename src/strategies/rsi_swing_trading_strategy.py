import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
from datetime import timedelta

# 1 week view RSI: above 30, heading up, will not touch it if it is below 30 or headed to 30 from 40
# I look through specific stocks I like that are good companies and don’t have any bad news coming out on them.

# DKNG FUBO LULU AFRM RBLX COIN CVNA ABNB FSLY BYND DDOG

# 1 day view RSI: below or near 30, especially if it hits 20-25

# 1 hr view RSI will most likely be below 30,
# buy when it starts to cross over 30, sell when it crosses 70 or is close to 70 with low buying volume or high selling volume
# (may have to tweak this, I haven’t always exited at the prime time)

SECOND = timedelta(seconds=1)
MINUTE = timedelta(minutes=1)


def calculate_rsi(data, window=14, ema=True):
    close_delta = data['close'].diff()
    # Make two series: one for lower closes and one for higher closes
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)

    if ema == True:
        # Use exponential moving average
        ma_up = up.ewm(com=window - 1, adjust=True).mean()
        ma_down = down.ewm(com=window - 1, adjust=True).mean()
    else:
        # Use simple moving average
        ma_up = up.rolling(window=window).mean()
        print(ma_up)
        ma_down = down.rolling(window=window).mean()

    rsi = ma_up / ma_down
    rsi = 100 - (100/(1 + rsi))
    return rsi


def calculate_stochastic_rsi(data, window=14):
    # Calculate RSI
    delta = data['close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=window - 1, adjust=True).mean()
    ema_down = down.ewm(com=window - 1, adjust=True).mean()
    rsi = ema_up / ema_down
    rsi = 100 - (100/(1 + rsi))

    # Calculate StochRSI
    stochrsi = (rsi - rsi.rolling(window=window).min()) / \
        (rsi.rolling(window=window).max() -
         rsi.rolling(window=window).min())

    return stochrsi


def calculate_bollinger_bands(data, window=20):
    sma = data['close'].rolling(window=window).mean()
    rstd = data['close'].rolling(window=window).std()
    upper_band = sma + 2 * rstd
    lower_band = sma - 2 * rstd
    return upper_band, lower_band


def calculate_keltner_channels(data, window=20):
    ema = data['close'].ewm(span=window, adjust=False).mean()
    atr = data['atr']
    upper_band = ema + (2 * atr)
    lower_band = ema - (2 * atr)
    return upper_band, lower_band


def backtest_rsi_strategy(data, hourly_data, rsi_entry_threshold=30, rsi_exit_threshold=70, days_under_threshold_number=14, ticker='FUBO', interval='1h', oversold_rsi_sma_threshold=20, overbought_rsi_sma_threshold=20):
    data['rsi'] = calculate_rsi(data, 14, False)
    data['position'] = 0
    data['trade_return'] = float(0)
    data['sma10'] = data['close'].rolling(window=10).mean()
    data['sma20'] = data['close'].rolling(window=20).mean()
    data['sma50'] = data['close'].rolling(window=50).mean()

    in_position = False
    entry_price = 0
    days_under_30 = 0
    had_position = False
    total_returns = 1  # Start with a multiplier of 1
    holding_periods = []  # List to store holding periods
    entry_date = None
    print('starting hourly new')
    return handle_post_initial_exit(
        data['date'].iloc[0], rsi_entry_threshold, rsi_exit_threshold, total_returns, hourly_data, oversold_rsi_sma_threshold, overbought_rsi_sma_threshold, ticker
    )
    # break
    # for i in range(1, len(data)):
    #     if had_position:
    #     # print(data['date'].iloc[i], data['rsi'].iloc[i])
    #     if not in_position and data['rsi'].iloc[i] < rsi_entry_threshold:
    #         days_under_30 += 1
    #         # print('days under 30', days_under_30)

    #     if not in_position and days_under_30 > days_under_threshold_number and data['rsi'].iloc[i] > rsi_entry_threshold:
    #         data.at[i, 'position'] = 1
    #         entry_price = data['close'].iloc[i]
    #         # Assuming 'date' is a column in your DataFrame
    #         entry_date = data['date'].iloc[i]
    #         # print('entry date', entry_date)
    #         # print('entry price', entry_price)
    #         in_position = True
    #         continue

    #     if not in_position and data['rsi'].iloc[i] > rsi_entry_threshold:
    #         days_under_30 = 0
    #         continue

    #     if in_position and data['rsi'].iloc[i] > rsi_exit_threshold and data['close'].iloc[i]:
    #         data.at[i, 'position'] = -1  # Sell
    #         exit_date = data['date'].iloc[i]
    #         current_price = data['close'].iloc[i]
    #         in_position = False
    #         days_under_30 = 0
    #         # print('exit price', current_price)
    #         # Calculate trade return
    #         trade_return = current_price / entry_price
    #         total_returns *= trade_return
    #         # print('trade return', trade_return, '%')
    #         # data['returns'] = trade_return
    #         data.at[i, 'trade_return'] = float(trade_return - 1)
    #         # print(data.iloc[i])
    #         print('exit date', exit_date)
    #         # Calculate holding period
    #         holding_period = (exit_date - entry_date).days
    #         # print('holding period', holding_period)
    #         holding_periods.append(holding_period)
    #         current_date = data['date'].iloc[i]
    #         had_position = True
    #         continue

    # #     total_returns = (total_returns - 1) * 100  # Convert to percentage
    # average_holding_period = sum(holding_periods) / \
    #     len(holding_periods) if holding_periods else 0
    # print('holding periods', holding_periods)
    # #     print(f"Total Strategy Returns only daily: {total_returns}%")
    # #     print(
    # #         f"Average Holding Period only daily: {average_holding_period} days")
    # #     data['total_strategy_returns'] = data['trade_return'].cumprod()
    # #     print('evaluating daily performance')
    # #     evaluate_performance(data)

    # #     current_date = data['date'].iloc[i]

    # # print('total returns', total_returns)
    # print('average holding period', average_holding_period)

    # return data


def get_data_for_backtest(current_date, hourly_data):

    current_unix = pd.to_datetime(current_date)

    hourly_data['datetime'] = pd.to_datetime(hourly_data['datetime'])

    data_slice_considering_current_date = hourly_data[hourly_data['datetime'] >= current_date]

    return data_slice_considering_current_date


def handle_post_initial_exit(current_date, rsi_entry_threshold, rsi_exit_threshold, total_returns, hourly_data, oversold_rsi_sma_threshold, overbought_rsi_sma_threshold, ticker
                             ):
    print('starting hourly', current_date)
    in_long_position = False
    in_short_position = False
    index_of_entry_long = None
    index_of_entry_short = None
    print(total_returns)
    total_returns_percent = total_returns
    should_ignore_next_long_signal = False
    should_ignore_next_short_signal = False

    in_position = in_long_position or in_short_position
    hourly_data = get_data_for_backtest(current_date, hourly_data)
    hourly_data['atr'] = hourly_data['high'] - hourly_data['low']

    upper_band, lower_band = calculate_keltner_channels(hourly_data, window=10)
    hourly_data['upper_band'] = upper_band
    hourly_data['lower_band'] = lower_band
    print('here')
    holding_periods = []  # List to store holding periods

    entry_price = 0
    hourly_data['rsi'] = calculate_rsi(hourly_data, 5, False)
    hourly_data['rsi_sma'] = hourly_data['rsi'].rolling(window=14).mean()

    hourly_data['position'] = 0
    hourly_data['trade_return'] = float(0)
    hourly_data['long_openings'] = False
    hourly_data['short_openings'] = False
    hourly_data['sma10'] = hourly_data['close'].rolling(window=10).mean()
    hourly_data['sma20'] = hourly_data['close'].rolling(window=20).mean()
    hourly_data['sma50'] = hourly_data['close'].rolling(window=50).mean()
    hourly_data['vwap'] = hourly_data['volume'] * hourly_data['close']
    stochastic_rsi = calculate_stochastic_rsi(hourly_data)

    hourly_data['stochastic_rsi'] = stochastic_rsi

    last_5_signals = deque(maxlen=5)

    # Start looking at the hourly chart after we've exited a position initiated on the daily chart - up to 2 times past 70 rsi
    # If it hits 70 rsi on the hourly chart, sell
    # If it hits 30 rsi on the hourly chart, buy
    for i in range(1, len(hourly_data)):

        current_rsi_sma = hourly_data['rsi_sma'].iloc[i]
        current_rsi = hourly_data['rsi'].iloc[i]
        # print('current rsi sma', current_rsi_sma)
        if math.isnan(current_rsi_sma) or current_rsi_sma is None:
            continue
        # print(hourly_data['datetime'].iloc[i], current_rsi)

        # Consider these as the opposite when shorting
        is_stock_oversold = current_rsi < rsi_entry_threshold
        is_stock_overbought = current_rsi > rsi_exit_threshold
        # print('jfdlska', current_rsi_sma, i)
        is_stock_oversold_sma = current_rsi_sma - \
            current_rsi > oversold_rsi_sma_threshold
        # print('is stock oversold sma', is_stock_oversold_sma)
        is_stock_overbought_sma = current_rsi - \
            current_rsi_sma > overbought_rsi_sma_threshold
        # print('is stock overbought sma', is_stock_overbought_sma)
        if is_stock_oversold_sma:
            signal = 1  # overbought
        elif is_stock_overbought_sma:
            signal = -1
        else:
            signal = 0

        last_5_signals.append(signal)

        if not in_position and not is_stock_oversold and not is_stock_overbought:
            # print(
            # 'not in position and had position and houly rsi is between 30 and 70, do nothing')
            continue

        # print('in long position', in_long_position)
        # print('in short position', in_short_position)
        # print('is stock oversold', is_stock_oversold)
        # print('is stock overbought', is_stock_overbought)

        [
            did_exit_long_position,
            new_total_returns_long,
            did_enter_long_position,
            new_index_of_entry_long,
            long_trade_return,
            short_trade_return_from_long,
        ] = handle_long_signal_positions_with_sma(in_long_position, is_stock_oversold_sma, is_stock_overbought_sma,
                                                  hourly_data, i, entry_price, holding_periods, total_returns, index_of_entry_long, in_short_position, index_of_entry_short)

        [
            did_exit_position_short,
            new_total_returns_short,
            did_enter_short_position,
            new_index_of_entry_short,
            short_trade_return,
            long_trade_return_from_short,
        ] = handle_short_signal_positions_with_sma(in_short_position, is_stock_oversold_sma, is_stock_overbought_sma,
                                                   hourly_data, i, entry_price, holding_periods, total_returns, index_of_entry_short, in_long_position, index_of_entry_long)

        # [
        #     did_exit_position_short,
        #     new_total_returns_short,
        #     did_enter_short_position,
        #     new_index_of_entry_short
        # ] = handle_short_positions(in_short_position, is_stock_oversold, is_stock_overbought,
        #                          hourly_data, i, entry_price, holding_periods, total_returns_percent, index_of_entry_short)

        # [
        #     did_exit_long_position,
        #     new_total_returns_long,
        #     did_enter_long_position,
        #     new_index_of_entry_long
        # ] = handle_long_signal_positions(in_long_position, is_stock_oversold, is_stock_overbought,
        #                                  hourly_data, i, entry_price, holding_periods, total_returns_percent, index_of_entry_long)
        # [
        #     did_exit_position_short,
        #     new_total_returns_short,
        #     did_enter_short_position,
        #     new_index_of_entry_short
        # ] = handle_short_positions(in_short_position, is_stock_oversold, is_stock_overbought,
        #                            hourly_data, i, entry_price, holding_periods, total_returns_percent, index_of_entry_short)

        did_exit_position = did_exit_long_position or did_exit_position_short

        if did_exit_position:
            if did_exit_long_position:
                # print('did exit long position')
                hourly_data.at[i, 'trade_return'] = float(
                    long_trade_return - 1)
                total_returns = new_total_returns_long
                in_long_position = False
                in_short_position = False
                # print('not in did exit long position')
                # print('new total returns long', new_total_returns_long)
            if did_exit_position_short:
                # print('did exit short position')
                hourly_data.at[i, 'trade_return'] = float(
                    short_trade_return - 1)
                total_returns = new_total_returns_short
                in_long_position = False
                in_short_position = False
                index_of_entry_short = None
                # print('not in did exit short position')
            #     print('new total returns short', new_total_returns_short)

        did_enter_position = did_enter_long_position or did_enter_short_position
        # or did_enter_short_position

        hourly_data.at[i, 'long_openings'] = is_stock_overbought_sma
        # print('yes', did_enter_long_position)
        hourly_data.at[i, 'short_openings'] = is_stock_oversold_sma
        # print('no', did_enter_short_position)

        if did_enter_position:
            in_position = True
            if did_enter_long_position:
                entry_date = hourly_data['datetime'].iloc[new_index_of_entry_long]
                # print('did enter long position', entry_date)
                in_long_position = True
                entry_price = hourly_data['close'].iloc[new_index_of_entry_long]
                index_of_entry_long = new_index_of_entry_long
                if short_trade_return_from_long:
                    total_returns = new_total_returns_long
                    hourly_data.at[i, 'trade_return'] = float(
                        short_trade_return_from_long - 1)
                # index_of_entry_long = None
                # print('not in did enter long position')
            if did_enter_short_position:
                entry_date = hourly_data['datetime'].iloc[new_index_of_entry_short]
                # print('did enter short position', entry_date)
                # print('new index of entry short', new_index_of_entry_short)
                in_short_position = True
                entry_price = hourly_data['close'].iloc[new_index_of_entry_short]
                index_of_entry_short = new_index_of_entry_short
                if long_trade_return_from_short:
                    total_returns = new_total_returns_short
                    hourly_data.at[i, 'trade_return'] = float(
                        long_trade_return_from_short - 1)
                # index_of_entry_short = None
                # print('not in did enter short position')

    # Calculate total strategy returns and average holding period
    print('alkdsj', total_returns)
    total_strategy_returns = (total_returns) * 100  # Convert to percentage
    print('avg holding periods')
    average_holding_period = sum(holding_periods) / \
        len(holding_periods) if holding_periods else 0

    print(f"Total Strategy Returns with hourly: {total_strategy_returns}%")
    print(f"Average Holding Period with hourly: {average_holding_period} days")
    plot_decision_points(hourly_data, ticker)
    total_return, sharpe_ratio, drawdown = evaluate_performance(
        hourly_data, 252*24*60)
    return total_return, sharpe_ratio, drawdown


def handle_short_positions(in_short_position, is_stock_oversold, is_stock_overbought, hourly_data, i, entry_price, holding_periods, total_returns_percent, index_of_entry_short):
    if not in_short_position and is_stock_overbought:
        entry_date_time = hourly_data['datetime'].iloc[i]
        # print('not in position and had position and rsi > 70')
        # print('Entering short position')
        hourly_data.at[i, 'position'] = -1  # Sell
        entry_price = hourly_data['close'].iloc[i]
        # print('short entry date', entry_date_time)
        # print('short entry price', entry_price)

        index_of_entry_short = i
        # print('index of entry short', index_of_entry_short)
        # Returns [did_exit_position, new_total_returns, did_enter_position, index_of_entry_short]
        return [False, None, True, index_of_entry_short]

    if in_short_position and is_stock_oversold:
        # print('in position and rsi < 30')
        # print('Exiting short position')
        hourly_data.at[i, 'position'] = 1  # Buy
        exit_date = hourly_data['datetime'].iloc[i]

        current_price = hourly_data['close'].iloc[i]
        in_short_position = False
        # print('short entry price', entry_price)
        # print('short exit date', exit_date)
        # print('short exit price', current_price)
        # print('short price difference', entry_price - current_price)
        # Calculate trade return
        trade_return = entry_price / current_price  # Reversed because we're shorting
        print('trade return short', trade_return, '%')

        total_returns_percent *= trade_return
        # print('total returns', total_returns)

        return [True, total_returns_percent, False, None]

    return [False, None, False, None]


# def handle_long_signal_positions_with_sma(in_long_position, is_stock_oversold_sma, is_stock_overbought_sma, hourly_data, i, entry_price, holding_periods, total_returns_percent, index_of_entry_long, in_short_position, index_of_entry_short):
#     take_profit = in_long_position and hourly_data['close'].iloc[i] > entry_price * 1.2
#     stop_loss = in_long_position and hourly_data['close'].iloc[i] < entry_price * .90
#     if not in_long_position and is_stock_overbought_sma:
#         entry_date_time = hourly_data['datetime'].iloc[i]
#         # print('should be opening long position', entry_date_time)
#         if entry_date_time.hour == 13 and entry_date_time.minute == 30:
#             return [False, None, False, None, None, None]

#         print('Entering long position')
#         hourly_data.at[i, 'position'] = 1
#         entry_price = hourly_data['close'].iloc[i]
#         # Assuming 'datetime' is a column in your DataFrame
#         # print('entry date', entry_date_time)
#         # print('entry price', entry_price)
#         short_trade_return_from_long = None
#         if in_short_position:
#             # print('exiting short position')
#             hourly_data.at[i, 'position'] = 1
#             exit_date = hourly_data['datetime'].iloc[i]
#             current_price = hourly_data['close'].iloc[i]
#             # print('exit date', exit_date)
#             entry_price = hourly_data['close'].iloc[index_of_entry_short]
#             # print('entry price short', entry_price)

#             # print('exit date', exit_date)
#             # print('entry price long', entry_price)
#             # print('entry price by index',
#             #       hourly_data['close'].iloc[index_of_entry_long])
#             # print('exit price', current_price)
#             # print('long price difference', current_price - entry_price)
#             # Calculate trade return
#             short_trade_return_from_long = entry_price / current_price
#             total_returns_percent *= short_trade_return_from_long
#             print('this will probably be big loss from a short position',
#                   short_trade_return_from_long)

#         index_of_entry_long = i
#         # Returns [did_exit_position, new_total_returns, did_enter_position, index_of_entry_long]
#         return [False, total_returns_percent, True, index_of_entry_long, None, short_trade_return_from_long]

#     if in_long_position and is_stock_overbought_sma or take_profit or stop_loss:
#         entry_date_time = hourly_data['datetime'].iloc[index_of_entry_long]
#         # print('entry date', entry_date_time)
#         # print('taking profit', take_profit)
#         # print('stopping loss', stop_loss)
#         # print('is stock overbought sma', is_stock_overbought_sma)
#         # print('not in position and had position and rsi > 70')
#         # print('Exiting long position')
#         hourly_data.at[i, 'position'] = -1
#         exit_date = hourly_data['datetime'].iloc[i]
#         current_price = hourly_data['close'].iloc[i]
#         # print('exit date', exit_date)
#         entry_price = hourly_data['close'].iloc[index_of_entry_long]
#         # print('entry price short', entry_price)

#         # print('exit date', exit_date)
#         # print('entry price long', entry_price)
#         # print('entry price by index',
#         #       hourly_data['close'].iloc[index_of_entry_long])
#         # print('exit price', current_price)
#         # print('long price difference', current_price - entry_price)
#         # print(entry_price)
#         # Calculate trade return
#         trade_return = current_price / entry_price
#         # print('exit datetime', exit_date)
#         # print('existing returns', total_returns_percent)
#         print('new returns', trade_return, '%', end='\n\n')
#         # print('new total', trade_return * total_returns_percent)
#         # print('index', i)
#         total_returns_percent *= trade_return
#         # print('total returns', total_returns)

#         # Calculate holding period
#         holding_period = (exit_date - entry_date_time).days
#         # print('holding period', holding_period, end='\n\n')
#         return [True, total_returns_percent, False, None, trade_return, None]
#     return [False, None, False, None, None, None]


def handle_long_signal_positions_with_sma(in_long_position, is_stock_oversold_sma, is_stock_overbought_sma, hourly_data, i, entry_price, holding_periods, total_returns_percent, index_of_entry_long, in_short_position, index_of_entry_short):
    take_profit = in_long_position and hourly_data['high'].iloc[i] > entry_price * 1.0015
    stop_loss = in_long_position and hourly_data['low'].iloc[i] < entry_price * .9985
    if not in_long_position and is_stock_overbought_sma:
        entry_date_time = hourly_data['datetime'].iloc[i]
        # print('should be opening long position', entry_date_time)
        if entry_date_time.hour == 13 and entry_date_time.minute == 30:
            return [False, None, False, None, None, None]

        # print('Entering long position', entry_date_time,
        #       hourly_data['stochastic_rsi'].iloc[i])
        hourly_data.at[i, 'position'] = 1
        entry_price = hourly_data['close'].iloc[i]
        # Assuming 'datetime' is a column in your DataFrame
        # print('entry date', entry_date_time)
        # print('entry price', entry_price)
        short_trade_return_from_long = None
        if in_short_position:
            # print('exiting short position')
            hourly_data.at[i, 'position'] = 1
            exit_date = hourly_data['datetime'].iloc[i]
            current_price = hourly_data['close'].iloc[i]
            # print('exit date', exit_date)
            entry_price = hourly_data['close'].iloc[index_of_entry_short]
            # print('entry price short', entry_price)
            # print('exit date', exit_date)
            # print('entry price long', entry_price)
            # print('entry price by index',
            #       hourly_data['close'].iloc[index_of_entry_long])
            # print('exit price', current_price)
            # print('long price difference', current_price - entry_price)
            # Calculate trade return
            short_trade_return_from_long = entry_price / current_price
            total_returns_percent *= short_trade_return_from_long
            print('this will probably be big loss from a short position',
                  short_trade_return_from_long, 'Stoch rsi of entry', hourly_data['stochastic_rsi'].iloc[index_of_entry_short], end='\n\n')

        index_of_entry_long = i
        # Returns [did_exit_position, new_total_returns, did_enter_position, index_of_entry_long]
        return [False, total_returns_percent, True, index_of_entry_long, None, short_trade_return_from_long]

    if in_long_position and (take_profit or stop_loss):
        entry_date_time = hourly_data['datetime'].iloc[index_of_entry_long]
        entry_price = hourly_data['close'].iloc[index_of_entry_long]
        current_price = hourly_data['close'].iloc[i]
        if take_profit:
            print('take profit', take_profit)
            current_price = hourly_data['high'].iloc[i]
        if stop_loss:
            print('stopping loss', stop_loss)
            current_price = hourly_data['low'].iloc[i]

        hourly_data.at[i, 'position'] = 0
        exit_date = hourly_data['datetime'].iloc[i]
        # print('exit date', exit_date)
        # print('entry price short', entry_price)

        # print('exit date', exit_date)
        # print('entry price long', entry_price)
        # print('entry price by index',
        #       hourly_data['close'].iloc[index_of_entry_long])
        # print('exit price', current_price)
        # print('long price difference', current_price - entry_price)
        # print(entry_price)
        # Calculate trade return
        trade_return = current_price / entry_price
        # print('exit datetime', exit_date)
        # print('existing returns', total_returns_percent)
        # print('Long trade return', trade_return, '%', 'Stoch rsi of entry',
        #       hourly_data['stochastic_rsi'].iloc[index_of_entry_long], end='\n\n')
        # print('new total', trade_return * total_returns_percent)
        # print('index', i)
        total_returns_percent *= trade_return
        # print('total returns', total_returns)

        # Calculate holding period
        holding_period = (exit_date - entry_date_time).days
        # print('holding period', holding_period, end='\n\n')
        return [True, total_returns_percent, False, None, trade_return, None]
    return [False, None, False, None, None, None]


def handle_short_signal_positions_with_sma(in_short_position, is_stock_oversold_sma, is_stock_overbought_sma, hourly_data, i, entry_price, holding_periods, total_returns_percent, index_of_entry_short, in_long_position, index_of_entry_long):
    take_profit = in_short_position and hourly_data['low'].iloc[i] < entry_price * .9985
    stop_loss = in_short_position and hourly_data['high'].iloc[i] > entry_price * 1.0015
    if not in_short_position and is_stock_oversold_sma:
        entry_date_time = hourly_data['datetime'].iloc[i]
        # print('Entering short position', entry_date_time)
        if entry_date_time.hour == 13 and entry_date_time.minute == 30:
            return [False, None, False, None, None, None]
        print('')
        hourly_data.at[i, 'position'] = -1
        entry_price = hourly_data['close'].iloc[i]
        # print('Entering short position',)  # entry_date_time, entry_price)
        # Assuming 'datetime' is a column in your DataFrame
        # print('entry date', entry_date_time)
        # print('entry price', entry_price)
        long_trade_return_from_short = None
        index_of_entry_short = i
        # Returns [did_exit_position, new_total_returns, did_enter_position, index_of_entry_long]
        if in_long_position:
            # print('exiting long position')
            hourly_data.at[i, 'position'] = -1
            exit_date = hourly_data['datetime'].iloc[i]
            current_price = hourly_data['close'].iloc[i]
            # print('exit date', exit_date)
            entry_price = hourly_data['close'].iloc[index_of_entry_long]
            # print('entry price short', entry_price)
            entry_date_time = hourly_data['datetime'].iloc[index_of_entry_long]
            # print('exit date', exit_date)
            # print('entry price long', entry_price)
            # print('entry price by index',
            #       hourly_data['close'].iloc[index_of_entry_long])
            # print('exit price', current_price)
            # print('long price difference', current_price - entry_price)
            # Calculate trade return
            long_trade_return_from_short = current_price / entry_price
            total_returns_percent *= long_trade_return_from_short
            # print('this will probably be big loss from a long position',
            #       long_trade_return_from_short, 'Stoch rsi of entry', hourly_data['stochastic_rsi'].iloc[index_of_entry_long])
            # holding_period = (exit_date - entry_date_time).seconds / 60
            # print('holding period', holding_period, end='\n\n')
        return [False, total_returns_percent, True, index_of_entry_short, None, long_trade_return_from_short]

    if in_short_position and (take_profit or stop_loss):
        entry_date_time = hourly_data['datetime'].iloc[index_of_entry_short]
        # print('entry date', entry_date_time)
        # print('taking profit', take_profit)
        # print('stopping loss', stop_loss)
        # print('not in position and had position and rsi > 70')
        # print('Exiting long position')
        current_price = hourly_data['close'].iloc[i]
        hourly_data.at[i, 'position'] = 0
        exit_date = hourly_data['datetime'].iloc[i]
        if take_profit:
            print('take profit', take_profit)
            current_price = hourly_data['low'].iloc[i]
        if stop_loss:
            print('stopping loss', stop_loss)
            current_price = hourly_data['high'].iloc[i]
        # print('exit date', exit_date)
        entry_price = hourly_data['close'].iloc[index_of_entry_short]
        # print('entry price short', entry_price)

        # print('exit date', exit_date)
        # print('entry price long', entry_price)
        # print('entry price by index',
        #       hourly_data['close'].iloc[index_of_entry_long])
        # print('exit price', current_price)
        # print('long price difference', current_price - entry_price)
        # print(entry_price)
        # Calculate trade return
        trade_return = entry_price / current_price
        # print('Short trade return', trade_return, '%', 'Stock rsi of entry',
        #       hourly_data['stochastic_rsi'].iloc[index_of_entry_short], end='\n\n')
        # print('exit datetime', exit_date)
        # print('existing returns', total_returns_percent)
        # print('exiting short position with return',
        #       trade_return, '%', end='\n\n')
        # print('new total', trade_return * total_returns_percent)
        # print('index', i)
        total_returns_percent *= trade_return
        # print('total returns', total_returns)

        # Calculate holding period
        holding_period = (exit_date - entry_date_time).seconds / 60
        print('holding period', holding_period, end='\n\n')
        return [True, total_returns_percent, False, None, trade_return, None]
    return [False, None, False, None, None, None]


def evaluate_performance(data, trading_periods=252):
    # Assuming 'trade_return' is a column in `data` representing returns of individual trades
    # Convert returns to a multiplier format (e.g., 0.05 for 5% return)
    data['trade_multiplier'] = 1 + data['trade_return']
    print('trade multiplier', data['trade_multiplier'].tail(20))

    # Cumulative return of the strategy
    total_return = data['trade_multiplier'].cumprod().iloc[-1]
    trading_periods = 252 * 6.5 * 60  # Modify as per the actual time frame
    risk_free_rate = 0.0541 / trading_periods
    data['minute_returns'] = data['trade_multiplier'].pct_change()
    data['excess_returns'] = data['minute_returns'] - risk_free_rate
    # Sharpe Ratio: Adjusted for minute data (if data is in minutes)
    # Assuming there are approximately 252 trading days in a year
    sharpe_ratio = np.sqrt(trading_periods) * (
        (data['minute_returns'].mean() - risk_free_rate) / data['minute_returns'].std())
    print('sharpe ratio', sharpe_ratio)
    # Maximum Drawdown
    cumulative_returns = data['trade_multiplier'].cumprod()
    # print('cumulative returns', cumulative_returns)
    drawdown = ((cumulative_returns.cummax() - cumulative_returns) /
                cumulative_returns.cummax()).max()
    print('drawdown', drawdown)

    # Average Holding Period
    # # Assuming `holding_periods` is a list containing the holding period for each trade in days
    # average_holding_period = sum(data['holding_periods']) / len(
    #     data['holding_periods']) if data['holding_periods'] else 0

    return total_return, sharpe_ratio, drawdown


def plot_decision_points(data, stock):
    # Assuming 'price' is your price column and 'decision' is the boolean decision column
    print('jlsfakj')
    plt.figure(figsize=(100, 60))
    # Plot the price data
    plt.plot(data.datetime, data['close'], label='close', color='blue')
    # plt.plot(data.datetime, data['rsi'], label='rsi', color='orange')
    # plt.plot(data.datetime, data['sma10'], label='sma10', color='orange')
    # plt.plot(data.datetime, data['sma20'], label='sma20', color='purple')
    # plt.plot(data.datetime, data['sma50'], label='sma50', color='green')
    # plt.plot(data.datetime, data['upper_band'],
    #          label='upper band', color='red')
    # plt.plot(data.datetime, data['lower_band'],
    #          label='lower band', color='green')

    # Identify decision points
    long_opportunities = data[data['long_openings'] == True]
    short_opportunities = data[data['short_openings'] == True]

    long_positions = data[data['position'] == 1]
    short_positions = data[data['position'] == -1]

    # Plot decision points
    plt.scatter(long_opportunities.datetime,
                long_opportunities['close'], color='red', marker='o', label='Long Entry')
    plt.scatter(short_opportunities.datetime,
                short_opportunities['close'], color='pink', marker='x', label='Short Entry')

    plt.scatter(long_positions.datetime,
                long_positions['close'], color='blue', marker='o', label='Long opens')
    plt.scatter(short_positions.datetime,
                short_positions['close'], color='purple', marker='x', label='Short opens')

    plt.title('Price Over Time with Decision Points')
    # plt.savefig(f'./{stock}.png')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()
    plt.show()

# Example usage
# plot_decision_points(your_dataframe)
