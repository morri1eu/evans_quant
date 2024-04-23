from src.alphas.all_alphas import alpha13
from src.strategies.portfolio import initialize_portfolio, update_portfolio

# Strategy for long positions based on alpha13
def alpha13_strategy_long(df, upper_bound):
    df = alpha13(df)  # Calculate alpha13 values
    
    # Initialize portfolio
    portfolio = initialize_portfolio(df)
    
    # Implement strategy
    for i in range(1, len(df)):
        if df['alpha13'].iloc[i] > upper_bound:
            # Buy at open, sell at close
            daily_return = df['close'].iloc[i] / df['open'].iloc[i] - 1
        else:
            daily_return = 0  # No action
            
        # Update portfolio
        portfolio = update_portfolio(portfolio, i, daily_return)
        
    return portfolio

# Strategy for short positions based on alpha13
def alpha13_strategy_short(df, lower_bound):
    df = alpha13(df)  # Calculate alpha13 values
    
    # Initialize portfolio
    portfolio = initialize_portfolio(df)
    
    # Implement strategy
    for i in range(1, len(df)):
        if df['alpha13'].iloc[i] < lower_bound:
            # Sell at open, buy at close (short)
            daily_return = df['open'].iloc[i] / df['close'].iloc[i] - 1
        else:
            daily_return = 0  # No action
            
        # Update portfolio
        portfolio = update_portfolio(portfolio, i, daily_return)
        
    return portfolio
