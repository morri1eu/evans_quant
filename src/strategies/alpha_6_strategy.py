from src.alphas.all_alphas import alpha6
import pandas as pd

def alpha_6_strategy_long(df, upper_bound):
    df['alpha6'] = alpha6(df)
    portfolio = pd.DataFrame(index=df.index)
    portfolio['Total'] = 100000  # Starting capital
    portfolio['Returns'] = 0
    
    for i in range(1, len(df)):
        if df['alpha6'].iloc[i] > upper_bound:
            daily_return = df['close'].iloc[i] / df['open'].iloc[i] - 1
        else:
            daily_return = 0
            
        portfolio.at[i, 'Returns'] = daily_return
        portfolio.at[i, 'Total'] = portfolio.at[i-1, 'Total'] * (1 + daily_return)
        
    return portfolio

def alpha_6_strategy_short(df, lower_bound):
    df['alpha6'] = alpha6(df)
    portfolio = pd.DataFrame(index=df.index)
    portfolio['Total'] = 100000  # Starting capital
    portfolio['Returns'] = 0
    
    for i in range(1, len(df)):
        if df['alpha6'].iloc[i] < -lower_bound:
            daily_return = df['open'].iloc[i] / df['close'].iloc[i] - 1
        else:
            daily_return = 0
            
        portfolio.at[i, 'Returns'] = daily_return
        portfolio.at[i, 'Total'] = portfolio.at[i-1, 'Total'] * (1 + daily_return)
        
    return portfolio
