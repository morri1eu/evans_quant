# Trading Bot Viability Task Breakdown

This plan assumes zero trading fees (Algolia) and allows rebuilding from scratch. Tasks are prioritized to make the system production-ready, with enough detail for an implementer to proceed.

## Priority 0: Foundations and Scope Agreement
- **Clarify requirements**: target markets (equities/crypto), timeframes (intraday vs swing), capital constraints, and compliance needs.
- **Decide rebuild vs refactor**: given current ad-hoc scripts and missing controls, favor a greenfield service with modular design; import only reusable ideas (e.g., ATR sizing) after tests exist.

## Priority 1: Architecture, Tooling, and Observability
- **Project skeleton**:
  - Package structure: `src/{data,strategies,execution,risk,backtest,live,shared}` with `pyproject.toml` for dependency locking and scripts.
  - Config: typed settings via `pydantic` or `dataclasses` loaded from YAML/ENV; single entrypoint for backtest and live modes.
- **Environment & CI**:
  - Pin Python version, add `ruff`/`black`/`mypy`/`pytest` configs, pre-commit hooks, GitHub Actions for lint + tests.
  - Containerize with `Dockerfile` and `docker-compose` (broker/data simulators, DB).
- **Logging & metrics**:
  - Structured logging (JSON) with request/trace IDs; send to stdout + file.
  - Metrics via Prometheus/OpenTelemetry; alerts for latency, error rate, position mismatches.

## Priority 2: Data Layer and Validation
- **Market data ingestion**:
  - Abstract data providers (e.g., Alpaca, Polygon, Binance) behind `DataClient` interface with methods `get_bars`, `stream_quotes`, `get_fundamentals`.
  - Add historical cache (Parquet/S3/local) with partitioning by symbol/date; fast retrieval via DuckDB/Polars.
- **Data quality checks**:
  - Schema validation (pydantic models) for OHLCV; drop/forward-fill gaps with explicit markers.
  - Clock synchronization and timezone handling; enforce monotonic timestamps.
  - Unit tests for edge cases: missing bars, duplicate timestamps, zero-volume candles.
- **Feature engine**:
  - Vectorized indicators (RSI, EMA, VWAP, ATR) via `ta`/`pandas`/`polars` with reproducible parameters stored in config.

## Priority 3: Backtesting & Research Framework
- **Reusable engine**:
  - Portfolio abstraction with cash, positions, PnL; supports multi-asset and intraday trading.
  - Order simulator with slippage models (even if fees=0) and partial fills; risk checks before fills.
  - Event-driven loop to test both bar-based and tick strategies.
- **Experiment management**:
  - Run configs saved with seeds; outputs as Parquet + JSON (metrics, trades, drawdowns).
  - Evaluation dashboards (e.g., `plotly`, `matplotlib`) for equity curves, factor exposures, turnover, and holding-time distributions.
- **Validation discipline**:
  - Train/validation/test splits by time; walk-forward or cross-validation for intraday signals.
  - Baseline comparisons vs buy-and-hold and naive mean-reversion to detect overfitting.

## Priority 4: Strategy Pipeline (fee-free assumption noted)
- **Signal library** (start simple, validate rigorously):
  - Momentum: EMA crossover with volatility-adjusted lookbacks; add trend filter (e.g., 200-period SMA) to reduce chop.
  - Mean reversion: RSI(14) with adaptive thresholds; Bollinger bands with z-score entries; VWAP fade with volume filter.
  - Regime detection: volatility states via ATR percentile or HMM; disable/adjust strategies in high-vol regimes.
- **Position sizing & exits**:
  - Kelly-fraction or volatility-scaled sizing capped by max exposure per asset/sector; since fees=0, still penalize turnover to avoid microstructure drag.
  - Stop types: ATR-based stops, time stops (bar count), trailing profit locks; unify via `ExitPolicy` interface.
- **Research examples**:
  - Notebook templates showing: data load → feature calc → signal labeling → backtest → performance report.
  - Include statistical tests (t-stats, hit rate, sharpe, sortino) and stability checks (rolling sharpe, drawdown clustering).

## Priority 5: Live Trading System
- **Execution service**:
  - Broker-agnostic `ExecutionClient` with implementations for target venues; supports limit/market/stop orders and cancels.
  - Idempotent order submission with retry/backoff; reconciliation loop to sync broker state to local book.
- **State management**:
  - Persistent store (PostgreSQL/SQLite) for positions, orders, fills, configs; snapshot/restore on restart.
  - Heartbeats and health checks; fail-safe kill switch on repeated errors or mismatched inventory.
- **Risk layer**:
  - Pre-trade checks: max position size, leverage caps, concentration limits, trading hours.
  - Post-trade controls: max intraday drawdown, daily loss limits, halt on abnormal slippage.
- **Orchestration**:
  - Scheduler for market sessions; worker process per strategy with shared risk/execution; message bus (Redis/NATS) for events.
  - Blue/green deploys with dry-run mode; shadow trading to compare live vs simulated fills.

## Priority 6: Monitoring, Reporting, and Operations
- **Dashboards**: live PnL, positions, risk limits, and latency; trade blotter with audit trail.
- **Alerts**: slack/email/pager for order failures, data lags, risk breach, and PnL drawdown.
- **Runbooks**: incident response steps, restart procedures, release checklist.

## Priority 7: Governance and Security
- **Secrets management**: vault or cloud KMS; no credentials in code.
- **Access controls**: least-privilege API keys; signing webhooks.
- **Compliance**: logging for auditability; disclaimers and guardrails for jurisdictional limits.

## Priority 8: Performance Tuning and Scaling
- **Optimization**: profile hot paths (indicator calc, backtests); leverage Polars/Numba for vectorized speedups.
- **Parallelism**: multiprocessing or Ray for multi-asset backtests and parameter sweeps.
- **Resilience**: autoscaling for data/strategy workers; chaos testing for provider outages.

## Deliverables Checklist (per milestone)
- Architecture doc + repo skeleton with CI and logging.
- Data clients with validation + tests; cached historical dataset.
- Backtest engine with slippage + risk checks; baseline reports.
- At least two validated strategies with notebooks and config-driven parameters.
- Live trading services (execution, risk, orchestration) with persistence and alerts.
- Ops runbooks and dashboards; security hardening and secrets management.
