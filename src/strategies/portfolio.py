import pandas as pd
import numpy as np

def initialize_portfolio(df):
  # Initialize portfolio
    portfolio = pd.DataFrame(index=df.index, dtype=np.float64)
    portfolio['Total'] = 100000.0  # Starting capital
    portfolio['Returns'] = np.zeros(len(df), dtype=np.float64)
    return portfolio

def update_portfolio(portfolio, i, daily_return):
    portfolio.at[i, 'Returns'] = daily_return
    portfolio.at[i, 'Total'] = portfolio.at[i-1, 'Total'] * (1 + daily_return)
    return portfolio