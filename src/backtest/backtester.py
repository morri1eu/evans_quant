# src/backtest/backtester.py
import pandas as pd
import multiprocessing
from src.dataparsers.alpha_input_data_helpers import calculate_metrics, calculate_signals
from src.alphas.all_alphas import *
import os
import time
from src.visualizations.generic_visualizations import plot_strategy, calculate_and_print_metrics, create_csv_from_metrics, calculate_mean_sharpe_ratio_from_metrics, create_df_from_metrics

def backtest(data, initial_capital):
    positions = pd.DataFrame(index=data.index).fillna(0.0)
    positions['Stock'] = 100 * data['Signal']
    portfolio = positions.multiply(data['Adj Close'], axis=0)
    pos_diff = positions.diff()
    portfolio['Holdings'] = (positions.multiply(data['Adj Close'], axis=0)).sum(axis=1)
    portfolio['Cash'] = initial_capital - (pos_diff.multiply(data['Adj Close'], axis=0)).sum(axis=1).cumsum()
    portfolio['Total'] = portfolio['Cash'] + portfolio['Holdings']
    portfolio['Returns'] = portfolio['Total'].pct_change()
    return portfolio

def get_data_for_backtest(stock_ticker, exchange):
    try:
        # read data from csv
        path = f'../data/baseline_data/{exchange}/{stock_ticker}_baseline.csv'
        data = pd.read_csv(path)
        
        # calculate metrics & indicators
        data_with_metrics = calculate_metrics(data)
        data_with_metrics_and_signals = calculate_signals(data_with_metrics)

        # return data
        return data_with_metrics_and_signals
    except:
        print(f'Error getting data for {stock_ticker}')
        return pd.DataFrame()

# def run_backtest(exchange='NASDAQ'):
#     # get list of stocks for exchange
#     stocks = get_stocks_for_exchange(exchange)

#     portfolios = []
#     stocks.sort()
#     metrics = []
#     # stocks_to_use = stocks[:100]
#     # loop through stocks
#     for stock_ticker in stocks:
#         # get data for backtest
#         data = get_data_for_backtest(stock_ticker, exchange)
#         # make sure data is not empty
        
#         if data.empty:
#             continue
#         # perform backtest
#         stock_portfolio = alpha_2_strategy(data, .25, -.25)
#         portfolios.append([stock_portfolio, stock_ticker])
#         # plot_strategy(data, stock_portfolio)
#         metrics.append(calculate_and_print_metrics(stock_portfolio, stock_ticker, False))
        
#     # return portfolios
#     create_csv_from_metrics(metrics, exchange, alpha_name='alpha_2')
#     return portfolios

def backtest_stock(stock_ticker, exchange, alpha_function_long, alpha_function_short, upper_bound, lower_bound):
    print('backtest stock', stock_ticker)
    data = get_data_for_backtest(stock_ticker, exchange)
    if data.empty:
        return None
    stock_portfolio_long = alpha_function_long(data, upper_bound)
    stock_portfolio_short = alpha_function_short(data, lower_bound)
    metrics_long = calculate_and_print_metrics(stock_portfolio_long, stock_ticker, False, data)
    metrics_short = calculate_and_print_metrics(stock_portfolio_short, stock_ticker, False, data)
    return stock_portfolio_long, stock_portfolio_short, metrics_long, metrics_short

def run_backtest_for_all_exchanges(alpha_name, alpha_function):
    exchanges = [name for name in os.listdir('../data/baseline_data') if os.path.isdir(os.path.join('../data/baseline_data', name))]
    try:
        for exchange in exchanges:
            run_backtest(alpha_name, alpha_function, exchange)
    except Exception as e:
        print(f'Error running backtest for {exchange}: {e}')

def run_backtest(alpha_function_long, alpha_function_short, upper_bound, lower_bound, exchange):
    stocks = get_stocks_for_exchange(exchange)
    stocks.sort()

    # Use all available CPUs or define the number you want to use
    num_processes = multiprocessing.cpu_count()
    print(f'Using {num_processes} processes')
    # Create a multiprocessing Pool
    with multiprocessing.Pool(num_processes) as pool:
        # Map backtest_stock function to all stocks
        results = pool.starmap(backtest_stock, [(stock, exchange, alpha_function_long, alpha_function_short, upper_bound, lower_bound) for stock in stocks])

    # Filter out None results if any stock data was empty
    results = [result for result in results if result is not None]
    
    # Separate the portfolios and metrics
    portfolios_long, portfolios_short, metrics_long, metrics_short = zip(*results)
    
    # Create CSV from metrics
    # create_csv_from_metrics(all_metrics, exchange, alpha_name)

    return portfolios_long, portfolios_short, metrics_long, metrics_short

def save_backtest_results(portfolios, exchange):
    # save results to csv
    for portfolio in portfolios:
        portfolio[0].to_csv(f'../data/backtest_results/{exchange}/{portfolio[1]}_backtest.csv')
    

def get_stocks_for_exchange(exchange='NASDAQ'):
    # get list of stocks for exchange
    stocks = os.listdir(f'../data/baseline_data/{exchange}')
    
    # extract tickers from filenames
    stock_tickers = [extract_ticker_from_filename(stock) for stock in stocks]
    return stock_tickers

def extract_ticker_from_filename(filename):
    return filename.split('_')[0]

def optimize_alpha_for_bounds_by_exchange(alpha_name, alpha_function_long, alpha_function_short, range, step_size, exchange):
    best_metric_upper = -np.inf
    best_metric_lower = -np.inf
    best_upper_bound = None
    best_lower_bound = None
    df_of_metrics_for_best_upper_bound = None
    df_of_metrics_for_best_lower_bound = None

    # Iterate over all possible combinations of upper and lower bounds
    for boundary in np.arange(range[0], range[1], step_size):
        # Ensure the upper bound is greater than the lower bound
        start = time.time()

        print(f'Running backtest for {alpha_name} with upper bound {boundary} and lower bound {-boundary} on {exchange}')
        # Backtest the strategy with the current set of bounds
        [portfolios_long, portfolios_short, metrics_long, metrics_short] = run_backtest(alpha_function_long, alpha_function_short, boundary, -boundary, exchange)

        # Evaluate the strategy's performance
        mean_sharpe_ratio_for_upper_bounds = calculate_mean_sharpe_ratio_from_metrics(metrics_long, boundary)
        mean_sharpe_ratio_for_lower_bounds = calculate_mean_sharpe_ratio_from_metrics(metrics_short, -boundary)

        # If the performance is better than what we've seen, store the bounds
        if mean_sharpe_ratio_for_upper_bounds > best_metric_upper:
            print('new best upper bound', boundary)
            best_metric_upper = mean_sharpe_ratio_for_upper_bounds
            best_upper_bound = boundary
            df_of_metrics_for_best_upper_bound = create_df_from_metrics(metrics_long, boundary)
        
        # If the performance is better than what we've seen, store the bounds
        if mean_sharpe_ratio_for_lower_bounds > best_metric_lower:
            print('new best lower bound', -boundary)
            best_metric_lower = mean_sharpe_ratio_for_lower_bounds
            best_lower_bound = -boundary
            df_of_metrics_for_best_lower_bound = create_df_from_metrics(metrics_short, -boundary)
        end = time.time()
        print(end - start)

    if not os.path.exists(f'../data/backtest_results/{exchange}/{alpha_name}'):
        os.makedirs(f'../data/backtest_results/{exchange}/{alpha_name}')
    
    df_of_metrics_for_best_upper_bound.to_csv(f'../data/backtest_results/{exchange}/{alpha_name}/long_metrics.csv')
    df_of_metrics_for_best_lower_bound.to_csv(f'../data/backtest_results/{exchange}/{alpha_name}/short_metrics.csv')

    print(f'Best upper bound for {alpha_name} on {exchange}: {best_upper_bound}, sharpe ratio: {best_metric_upper}')
    print(f'Best lower bound for {alpha_name} on {exchange}: {best_lower_bound}, sharpe ratio: {best_metric_lower}')
    return best_upper_bound, best_metric_upper, best_lower_bound, best_metric_lower

def optimize_alpha_for_bounds_all_exchanges(alpha_name, alpha_function_long, alpha_function_short, range, step_size, exchange):
    exchanges = [name for name in os.listdir('../data/baseline_data') if os.path.isdir(os.path.join('../data/baseline_data', name))]
    try:
        for exchange in exchanges:
            optimize_alpha_for_bounds_by_exchange(alpha_name, alpha_function_long, alpha_function_short, range, step_size, exchange)
    except Exception as e:
        print(f'Error running backtest for {exchange}: {e}')
