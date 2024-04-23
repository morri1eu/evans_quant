# src/strategies/moving_average_crossover.py
import pandas as pd

def apply_moving_average_strategy(data, short_window, long_window):
    data['Short_MA'] = data['Close'].rolling(window=short_window).mean()
    data['Long_MA'] = data['Close'].rolling(window=long_window).mean()
    data['Signal'] = 0.0
    data.loc[data['Short_MA'] > data['Long_MA'], 'Signal'] = 1.0
    data['Position'] = data['Signal'].diff()
    return data
