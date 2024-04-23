from src.alphas.all_alphas import alpha4
import pandas as pd
from src.strategies.portfolio import initialize_portfolio

def alpha_4_strategy_long(df, upper_bound):
    # Calculate alpha4 values
    print('calculating alpha4')
    print(df['low'])
    df['alpha4'] = alpha4(df)
    
    print('batman')
    # Initialize portfolio
    portfolio = initialize_portfolio(df)
    
    # Implement strategy
    for i in range(1, len(df)):
        if df['alpha4'].iloc[i] > upper_bound:
            # Buy at open, sell at close
            daily_return = df['close'].iloc[i] / df['open'].iloc[i] - 1
        else:
            daily_return = 0  # No action
            
        # Update portfolio
        portfolio.at[i, 'Returns'] = daily_return
        portfolio.at[i, 'Total'] = portfolio.at[i-1, 'Total'] * (1 + daily_return)
        
    return portfolio

def alpha_4_strategy_short(df, lower_bound):
    # Calculate alpha4 values
    df['alpha4'] = alpha4(df)
    
    # Initialize portfolio
    portfolio = initialize_portfolio(df)
    
    # Implement strategy
    for i in range(1, len(df)):
        if df['alpha4'].iloc[i] < lower_bound:
            # Sell at open, buy at close (short)
            daily_return = df['open'].iloc[i] / df['close'].iloc[i] - 1
        else:
            daily_return = 0  # No action
            
        # Update portfolio
        portfolio.at[i, 'Returns'] = daily_return
        portfolio.at[i, 'Total'] = portfolio.at[i-1, 'Total'] * (1 + daily_return)
        
    return portfolio
    