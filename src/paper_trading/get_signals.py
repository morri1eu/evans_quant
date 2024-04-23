from src.backtest.backtester import optimize_alpha_for_bounds_by_exchange
from src.paper_trading.paper_strategies.alpha_1_paper import generate_alpha_1_paper_long_signal, generate_alpha_1_paper_short_signal
import pandas as pd


from src.dataparsers.alpha_input_data_helpers import calculate_metrics, calculate_signals


def get_signals_for_exchange(exchange, alpha_name):
    # Load the data
    data = pd.read_csv(
        f'../data/backtest_results/{exchange}/{alpha_name}/long_metrics.csv')
    data_short = pd.read_csv(
        f'../data/backtest_results/{exchange}/{alpha_name}/short_metrics.csv')

    dropped = data.dropna()
    # Sort by Sharpe Ratio
    stocks_sorted_by_sharpe = dropped.sort_values("Sharpe Ratio")

    stocks_sorted_by_sharpe_short = data_short.dropna().sort_values("Sharpe Ratio")

    # Get the top stocks by sharpe ratio that I will trade
    top_stocks = stocks_sorted_by_sharpe.tail(50)
    top_stocks_short = stocks_sorted_by_sharpe_short.tail(50)
    print('batman')
    print(top_stocks)

    top_stocks_total_return = top_stocks.sort_values("Total Return")

    top_stocks_total_return_short = top_stocks_short.sort_values(
        "Total Return")
    # Init Alpaca

    # Go to my paper trading account and get the balance

    # Split the balance into 5% chunks

    # Generate Signals

    long_signals = []

    for stock in top_stocks.iterrows():
        # Get the data for the stock
        print('klfshdkla')

        ticker = stock[1]['Stock']

        boundary = stock[1]['Bound']
        print(boundary)
        # adjusted_boundary = boundary * 1.1
        df = pd.read_csv(
            f'../data/baseline_data/{exchange}/{ticker}_baseline.csv')
        df_with_metrics = calculate_metrics(df)
        df_with_metrics_and_signals = calculate_signals(df_with_metrics)

        long_signals.append([ticker, generate_alpha_1_paper_long_signal(
            df_with_metrics_and_signals, boundary, ticker)])
        buys = 0
        for signal in long_signals:
            if signal[1]:
                buys = buys + 1
        print(buys)

    short_signals = []
    for stock in top_stocks_short.iterrows():
        # Get the data for the stock
        print('klfshdkla')

        ticker = stock[1]['Stock']

        boundary = stock[1]['Bound']
        print(boundary)
        # adjusted_boundary = boundary * 1.1
        df = pd.read_csv(
            f'../data/baseline_data/{exchange}/{ticker}_baseline.csv')
        df_with_metrics = calculate_metrics(df)
        df_with_metrics_and_signals = calculate_signals(df_with_metrics)

        short_signals.append([ticker, generate_alpha_1_paper_short_signal(
            df_with_metrics_and_signals, boundary, ticker)])
        buys = 0
        for signal in short_signals:
            if signal[1]:
                buys = buys + 1
        print(buys)

    return [long_signals, short_signals]
