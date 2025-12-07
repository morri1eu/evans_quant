import logging
import multiprocessing
import os
import time
from typing import Callable, Tuple

import numpy as np
import pandas as pd

from src.alphas.all_alphas import *
from src.backtest.config import BacktestConfig
from src.dataparsers.alpha_input_data_helpers import calculate_metrics, calculate_signals
from src.visualizations.generic_visualizations import (
    calculate_and_print_metrics,
    calculate_mean_sharpe_ratio_from_metrics,
    create_csv_from_metrics,
    create_df_from_metrics,
    plot_strategy,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _normalize_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names so downstream functions can rely on snake_case."""

    data = data.copy()
    data.columns = [col.strip().lower().replace(" ", "_") for col in data.columns]
    return data


def _ensure_required_columns(data: pd.DataFrame, config: BacktestConfig) -> pd.DataFrame:
    missing = [col for col in config.required_columns if col not in data.columns]
    if missing:
        logger.error("Missing required columns: %s", ", ".join(missing))
        return pd.DataFrame()
    return data


def _pick_price_column(data: pd.DataFrame, config: BacktestConfig) -> str:
    for candidate in config.price_column_candidates():
        if candidate in data.columns:
            return candidate
    raise ValueError("No recognized price column found; looked for adj_close, close, price")


def _compute_atr(data: pd.DataFrame, window: int) -> pd.Series:
    true_range = pd.concat(
        [
            (data["high"] - data["low"]),
            (data["high"] - data["close"].shift()).abs(),
            (data["low"] - data["close"].shift()).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = true_range.rolling(window=window, min_periods=1).mean()
    return atr


def _calculate_position_sizes(data: pd.DataFrame, price_col: str, config: BacktestConfig) -> pd.Series:
    atr = data.get("atr")
    if atr is None:
        atr = _compute_atr(data, config.atr_window)
    atr = atr.clip(lower=1e-4).fillna(method="ffill")

    per_trade_risk = config.initial_capital * config.risk_per_trade
    raw_sizes = (per_trade_risk / (atr * config.atr_multiplier)).clip(lower=0)

    max_position_value = config.initial_capital * config.max_position_value_pct
    value_limited_sizes = (max_position_value / data[price_col]).clip(lower=0)

    sizes = np.floor(np.minimum(raw_sizes, value_limited_sizes)).astype(int)
    return sizes


def backtest(data: pd.DataFrame, config: BacktestConfig | None = None) -> pd.DataFrame:
    config = config or BacktestConfig()
    data = _normalize_columns(data)
    data = _ensure_required_columns(data, config)
    if data.empty:
        return pd.DataFrame()

    data_with_metrics = calculate_metrics(data)
    data_with_metrics_and_signals = calculate_signals(data_with_metrics)

    if "signal" not in data_with_metrics_and_signals.columns:
        logger.error("Cannot run backtest without a 'signal' column in the dataset.")
        return pd.DataFrame()

    price_col = _pick_price_column(data_with_metrics_and_signals, config)
    position_sizes = _calculate_position_sizes(data_with_metrics_and_signals, price_col, config)

    positions = pd.DataFrame(index=data_with_metrics_and_signals.index).fillna(0.0)
    positions["stock_shares"] = position_sizes * data_with_metrics_and_signals["signal"]

    portfolio = positions.multiply(data_with_metrics_and_signals[price_col], axis=0)
    pos_diff = positions.diff()

    trade_costs = (pos_diff.abs() * config.transaction_cost_per_share).multiply(
        data_with_metrics_and_signals[price_col], axis=0
    )

    portfolio["Holdings"] = (positions.multiply(data_with_metrics_and_signals[price_col], axis=0)).sum(axis=1)
    portfolio["Cash"] = config.initial_capital - (
        (pos_diff.multiply(data_with_metrics_and_signals[price_col], axis=0)).sum(axis=1).cumsum()
        + trade_costs.sum(axis=1).cumsum()
    )
    portfolio["Total"] = portfolio["Cash"] + portfolio["Holdings"]
    portfolio["Returns"] = portfolio["Total"].pct_change()
    portfolio["Drawdown"] = portfolio["Total"] / portfolio["Total"].cummax() - 1
    return portfolio


def get_data_for_backtest(stock_ticker: str, exchange: str, config: BacktestConfig | None = None) -> pd.DataFrame:
    config = config or BacktestConfig()
    try:
        path = f"../data/baseline_data/{exchange}/{stock_ticker}_baseline.csv"
        data = pd.read_csv(path)
        data = _normalize_columns(data)
        data = _ensure_required_columns(data, config)
        if data.empty:
            return pd.DataFrame()

        data_with_metrics = calculate_metrics(data)
        data_with_metrics_and_signals = calculate_signals(data_with_metrics)
        return data_with_metrics_and_signals
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Error getting data for %s: %s", stock_ticker, exc)
        return pd.DataFrame()


def backtest_stock(
    stock_ticker: str,
    exchange: str,
    alpha_function_long: Callable,
    alpha_function_short: Callable,
    upper_bound: float,
    lower_bound: float,
    config: BacktestConfig | None = None,
):
    logger.info("Backtesting %s", stock_ticker)
    data = get_data_for_backtest(stock_ticker, exchange, config)
    if data.empty:
        return None
    stock_portfolio_long = alpha_function_long(data, upper_bound)
    stock_portfolio_short = alpha_function_short(data, lower_bound)
    metrics_long = calculate_and_print_metrics(stock_portfolio_long, stock_ticker, False, data)
    metrics_short = calculate_and_print_metrics(stock_portfolio_short, stock_ticker, False, data)
    return stock_portfolio_long, stock_portfolio_short, metrics_long, metrics_short


def run_backtest_for_all_exchanges(alpha_name: str, alpha_function: Callable):
    exchanges = [
        name
        for name in os.listdir("../data/baseline_data")
        if os.path.isdir(os.path.join("../data/baseline_data", name))
    ]
    try:
        for exchange in exchanges:
            run_backtest(alpha_name, alpha_function, exchange)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Error running backtest for %s: %s", exchange, exc)


def run_backtest(
    alpha_function_long: Callable,
    alpha_function_short: Callable,
    upper_bound: float,
    lower_bound: float,
    exchange: str,
    config: BacktestConfig | None = None,
):
    config = config or BacktestConfig()
    stocks = get_stocks_for_exchange(exchange)
    stocks.sort()

    num_processes = multiprocessing.cpu_count()
    logger.info("Using %s processes", num_processes)

    with multiprocessing.Pool(num_processes) as pool:
        results = pool.starmap(
            backtest_stock,
            [
                (stock, exchange, alpha_function_long, alpha_function_short, upper_bound, lower_bound, config)
                for stock in stocks
            ],
        )

    results = [result for result in results if result is not None]

    if not results:
        return [], [], [], []

    portfolios_long, portfolios_short, metrics_long, metrics_short = zip(*results)

    return portfolios_long, portfolios_short, metrics_long, metrics_short


def save_backtest_results(portfolios: list[Tuple[pd.DataFrame, str]], exchange: str):
    for portfolio in portfolios:
        portfolio[0].to_csv(f"../data/backtest_results/{exchange}/{portfolio[1]}_backtest.csv")


def get_stocks_for_exchange(exchange: str = "NASDAQ"):
    stocks = os.listdir(f"../data/baseline_data/{exchange}")
    stock_tickers = [extract_ticker_from_filename(stock) for stock in stocks]
    return stock_tickers


def extract_ticker_from_filename(filename: str):
    return filename.split("_")[0]


def optimize_alpha_for_bounds_by_exchange(
    alpha_name: str,
    alpha_function_long: Callable,
    alpha_function_short: Callable,
    range: tuple,
    step_size: float,
    exchange: str,
):
    best_metric_upper = -np.inf
    best_metric_lower = -np.inf
    best_upper_bound = None
    best_lower_bound = None
    df_of_metrics_for_best_upper_bound = None
    df_of_metrics_for_best_lower_bound = None

    for boundary in np.arange(range[0], range[1], step_size):
        start = time.time()
        logger.info(
            "Running backtest for %s with upper bound %s and lower bound %s on %s",
            alpha_name,
            boundary,
            -boundary,
            exchange,
        )
        [portfolios_long, portfolios_short, metrics_long, metrics_short] = run_backtest(
            alpha_function_long, alpha_function_short, boundary, -boundary, exchange
        )

        if not metrics_long or not metrics_short:
            logger.warning("No metrics returned for %s at bound %s", exchange, boundary)
            continue

        mean_sharpe_ratio_for_upper_bounds = calculate_mean_sharpe_ratio_from_metrics(metrics_long, boundary)
        mean_sharpe_ratio_for_lower_bounds = calculate_mean_sharpe_ratio_from_metrics(metrics_short, -boundary)

        if mean_sharpe_ratio_for_upper_bounds > best_metric_upper:
            logger.info("New best upper bound %s", boundary)
            best_metric_upper = mean_sharpe_ratio_for_upper_bounds
            best_upper_bound = boundary
            df_of_metrics_for_best_upper_bound = create_df_from_metrics(metrics_long, boundary)

        if mean_sharpe_ratio_for_lower_bounds > best_metric_lower:
            logger.info("New best lower bound %s", -boundary)
            best_metric_lower = mean_sharpe_ratio_for_lower_bounds
            best_lower_bound = -boundary
            df_of_metrics_for_best_lower_bound = create_df_from_metrics(metrics_short, -boundary)
        end = time.time()
        logger.info("Completed bound sweep step in %.2fs", end - start)

    os.makedirs(f"../data/backtest_results/{exchange}/{alpha_name}", exist_ok=True)

    if df_of_metrics_for_best_upper_bound is not None:
        df_of_metrics_for_best_upper_bound.to_csv(
            f"../data/backtest_results/{exchange}/{alpha_name}/long_metrics.csv"
        )
    if df_of_metrics_for_best_lower_bound is not None:
        df_of_metrics_for_best_lower_bound.to_csv(
            f"../data/backtest_results/{exchange}/{alpha_name}/short_metrics.csv"
        )

    logger.info(
        "Best upper bound for %s on %s: %s, sharpe ratio: %s",
        alpha_name,
        exchange,
        best_upper_bound,
        best_metric_upper,
    )
    logger.info(
        "Best lower bound for %s on %s: %s, sharpe ratio: %s",
        alpha_name,
        exchange,
        best_lower_bound,
        best_metric_lower,
    )
    return best_upper_bound, best_metric_upper, best_lower_bound, best_metric_lower


def optimize_alpha_for_bounds_all_exchanges(
    alpha_name: str,
    alpha_function_long: Callable,
    alpha_function_short: Callable,
    range: tuple,
    step_size: float,
    exchange: str,
):
    exchanges = [
        name
        for name in os.listdir("../data/baseline_data")
        if os.path.isdir(os.path.join("../data/baseline_data", name))
    ]
    try:
        for exchange in exchanges:
            optimize_alpha_for_bounds_by_exchange(
                alpha_name, alpha_function_long, alpha_function_short, range, step_size, exchange
            )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Error running backtest for %s: %s", exchange, exc)
