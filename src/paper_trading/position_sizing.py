# position_sizer.py

def calculate_position_sizes(signals, buying_power, risk_per_trade, stop_loss_percent):
    """
    Calculate the position sizes for each stock based on the buying power, risk per trade, and stop loss percentage.

    :param signals: The signals for each stock.
    :param buying_power: Total buying power available in the account.
    :param risk_per_trade: The percentage of the account you're willing to risk on a single trade.
    :param stop_loss_percent: The stop loss percentage for the trade.
    :return: The position sizes for each stock.
    """
    # Calculate the dollar risk per trade
    dollar_risk_per_trade = buying_power * risk_per_trade

    # Calculate the position size based on the stop loss
    position_with_sizes = []
    for [stock_ticker, signal] in signals:
        if signal:
            position_size = dollar_risk_per_trade / stop_loss_percent
            position_with_sizes.append([stock_ticker, position_size])

    return position_with_sizes


def calculate_position_size(stock_ticker, buying_power, risk_per_trade, stop_loss_percent):
    """
    Calculate the position size based on the buying power, risk per trade, and stop loss percentage.

    :param buying_power: Total buying power available in the account.
    :param risk_per_trade: The percentage of the account you're willing to risk on a single trade.
    :param stop_loss_percent: The stop loss percentage for the trade.
    :return: The dollar amount to be invested in the trade.
    """
    # Calculate the dollar risk per trade
    dollar_risk_per_trade = buying_power * risk_per_trade

    # Calculate the position size based on the stop loss
    position_size = dollar_risk_per_trade / stop_loss_percent

    return [stock_ticker, position_size]


def adjust_position_for_volatility(position_size, volatility):
    """
    Adjust the position size for the volatility of the stock.

    :param position_size: The initial position size calculated.
    :param volatility: The volatility measure of the stock (e.g., ATR).
    :return: The adjusted position size.
    """
    # Adjust position size inversely to volatility
    # The higher the volatility, the smaller the position size should be
    adjusted_position_size = position_size / volatility

    return adjusted_position_size

# Example usage:
# buying_power = alpaca_manager.get_buying_power()
# risk_per_trade = 0.01  # 1% risk per trade
# stop_loss_percent = 0.05  # 5% stop loss
# volatility = 2.5  # Example volatility measure (e.g., ATR)

# position_size = calculate_position_size(buying_power, risk_per_trade, stop_loss_percent)
# adjusted_position_size = adjust_position_for_volatility(position_size, volatility)
