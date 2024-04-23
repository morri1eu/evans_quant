# src/strategies/moving_average_crossover.py
import pandas as pd
from src.alphas.all_alphas import alpha1
from src.utils.functions_and_operators import stddev
from src.dataparsers.alpha_input_data_helpers import extract_returns_from_df
from src.strategies.portfolio import initialize_portfolio
import numpy as np

def alpha_1_strategy_long(df, upper_bound):
    # Calculate alpha1 values
    df['alpha1'] = alpha1(df).last()

    # Initialize portfolio
    portfolio = initialize_portfolio(df)
    
    # Implement strategy
    for i in range(1, len(df)):
        if df['alpha1'].iloc[i] > upper_bound:
            # Buy at open, sell at close
            daily_return = df['close'].iloc[i] / df['open'].iloc[i] - 1
        else:
            daily_return = 0  # No action
            
        # Update portfolio
        portfolio.at[i, 'Returns'] = daily_return
        portfolio.at[i, 'Total'] = portfolio.at[i-1, 'Total'] * (1 + daily_return)
        
    return portfolio

def alpha_1_strategy_short(df, lower_bound):
    # Calculate alpha1 values
    df['alpha1'] = alpha1(df)

    # Initialize portfolio
    portfolio = initialize_portfolio(df)
    
    # Implement strategy
    for i in range(1, len(df)):
        if df['alpha1'].iloc[i] < lower_bound:
            # Sell at open, buy at close (short)
            daily_return = df['open'].iloc[i] / df['close'].iloc[i] - 1
        else:
            daily_return = 0  # No action
            
        # Update portfolio
        portfolio.at[i, 'Returns'] = daily_return
        portfolio.at[i, 'Total'] = portfolio.at[i-1, 'Total'] * (1 + daily_return)
        
    return portfolio

# def run_alpha_1_over_exchange(exchange, upper_bound, lower_bound):
#     # get list of stocks for exchange
#     stocks = 
#     # Read data from csv
#     path = f'../data/baseline_data/{exchange}/{exchange}_baseline.csv'
#     df = pd.read_csv(path)
    
#     # Apply strategy
#     portfolio = alpha_1_strategy(df, upper_bound, lower_bound)
    
#     # Return portfolio
#     return portfolio