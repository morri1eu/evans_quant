from src.alphas.all_alphas import alpha1
import pandas as pd


def generate_alpha_1_paper_long_signal(df, upper_bound, stock_ticker):
    df['alpha1'] = alpha1(df)
    signal = df['alpha1'].iloc[-1]
    print('alpha1: ', stock_ticker, signal)
    return signal > upper_bound


def generate_alpha_1_paper_short_signal(df, lower_bound, stock_ticker):
    df['alpha1'] = alpha1(df)
    signal = df['alpha1'].iloc[-1]
    print('alpha1: ', stock_ticker, signal)
    return signal < lower_bound

# 10 and 50 day moving average cross the 200 moving day average from below buying opportunity
# Month view drops below RSI of 30
#
