# src/strategies/moving_average_crossover.py
import pandas as pd
from src.alphas.all_alphas import alpha2
from src.utils.functions_and_operators import stddev
from src.dataparsers.alpha_input_data_helpers import extract_returns_from_df
import numpy as np
from src.strategies.portfolio import initialize_portfolio

def alpha_2_strategy_long(df, upper_bound):
    # Calculate alpha2 values
    df['alpha2'] = alpha2(df)
    print(df['alpha2'])
    print('mean: ', df['alpha2'].mean())
    print('stddev: ', df['alpha2'].std())
    print('median: ', df['alpha2'].median())
    print('max: ', df['alpha2'].max())
    print('min: ', df['alpha2'].min())
    # Initialize portfolio
    portfolio = initialize_portfolio(df)
    
    # Implement strategy
    for i in range(1, len(df)):
        if df['alpha2'].iloc[i] > upper_bound:
            # Buy at open, sell at close
            daily_return = df['close'].iloc[i] / df['open'].iloc[i] - 1
        else:
            daily_return = 0  # No action
            
        # Update portfolio
        portfolio.at[i, 'Returns'] = daily_return
        portfolio.at[i, 'Total'] = portfolio.at[i-1, 'Total'] * (1 + daily_return)
        
    return portfolio

def alpha_2_strategy_short(df, lower_bound):
    # Calculate alpha2 values
    df['alpha2'] = alpha2(df)

    # Initialize portfolio
    portfolio = initialize_portfolio(df)
    
    # Implement strategy
    for i in range(1, len(df)):
        if df['alpha2'].iloc[i] < lower_bound:
            # Sell at open, buy at close (short)
            daily_return = df['open'].iloc[i] / df['close'].iloc[i] - 1
        else:
            daily_return = 0  # No action
            
        # Update portfolio
        portfolio.at[i, 'Returns'] = daily_return
        portfolio.at[i, 'Total'] = portfolio.at[i-1, 'Total'] * (1 + daily_return)
        
    return portfolio
