from dataclasses import dataclass
from typing import List


@dataclass
class BacktestConfig:
    """Configuration for backtests to control risk and sizing rules."""

    initial_capital: float = 100_000.0
    risk_per_trade: float = 0.01  # risk 1% of equity per trade
    max_position_value_pct: float = 0.2  # cap any single position to 20% of equity
    atr_multiplier: float = 1.5  # scale ATR to approximate stop distance
    transaction_cost_per_share: float = 0.005  # simple per-share commission/slippage estimate
    required_columns: List[str] = (
        "close",
        "high",
        "low",
        "volume",
    )
    atr_window: int = 14

    def price_column_candidates(self) -> List[str]:
        return ["adj_close", "close", "price"]
