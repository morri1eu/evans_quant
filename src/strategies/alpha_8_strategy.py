from src.alphas.all_alphas import alpha8
import pandas as pd
from src.strategies.portfolio import initialize_portfolio

def alpha_8_strategy_long(df, upper_bound):
    df['alpha8'] = alpha8(df)
    portfolio = initialize_portfolio(df)
    
    for i in range(1, len(df)):
        if df['alpha8'].iloc[i] > upper_bound:
            daily_return = df['close'].iloc[i] / df['open'].iloc[i] - 1
        else:
            daily_return = 0
            
        portfolio.loc['Returns'].iloc[i] = daily_return
        portfolio.loc['Total'].iloc[i] = portfolio.loc['Total'].iloc[i-1] * (1 + daily_return)
        
    return portfolio

def alpha_8_strategy_short(df, lower_bound):
    df['alpha8'] = alpha8(df)
    portfolio = initialize_portfolio(df)
    
    for i in range(1, len(df)):
        if df['alpha8'].iloc[i] < -lower_bound:
            daily_return = df['open'].iloc[i] / df['close'].iloc[i] - 1
        else:
            daily_return = 0
            
        portfolio.at[i, 'Returns'] = daily_return
        portfolio.at[i, 'Total'] = portfolio.at[i-1, 'Total'] * (1 + daily_return)
        
    return portfolio