# entry_points/moving_average_entry.py
from src.utils.data_fetcher import fetch_data
from src.strategies.moving_average_crossover import apply_moving_average_strategy
from src.backtest.backtester import backtest
from src.visualizations.generic_visualizations import plot_strategy, calculate_and_print_metrics

def run_moving_average_strategy(stock_ticker='AAPL', start_date='2020-01-01', end_date='2021-01-01', short_window=40, long_window=100, funds=100000.0):
    # Fetch historical data
    data = fetch_data(stock_ticker, start_date, end_date)

    # Apply moving average crossover strategy
    data = apply_moving_average_strategy(data, short_window, long_window)

    # Perform backtesting
    portfolio = backtest(data, funds)

    # Plot strategy and portfolio value
    plot_strategy(data, portfolio, strategy_name='Moving Average Crossover')

    # Calculate and print metrics
    calculate_and_print_metrics(portfolio)

    return portfolio
