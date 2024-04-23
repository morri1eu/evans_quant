from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest, MarketOrderRequest, LimitOrderRequest, StopOrderRequest, StopLimitOrderRequest, GetOrdersRequest, ClosePositionRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from alpaca.common.enums import BaseURL
from src.paper_trading.position_sizing import calculate_position_sizes, calculate_position_size, adjust_position_for_volatility
from dotenv import load_dotenv
import os
from alpaca.trading.stream import TradingStream
import asyncio


class AlpacaManager:
    env = load_dotenv()
    ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
    ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")

    def __init__(self, stock_list):
        print('in alpaca manager init',
              self.ALPACA_API_KEY, self.ALPACA_SECRET_KEY)
        self.api = TradingClient(
            self.ALPACA_API_KEY, self.ALPACA_SECRET_KEY, paper=True)
        self.websocket = TradingStream(
            self.ALPACA_API_KEY, self.ALPACA_SECRET_KEY, paper=True)

        self.account = self.api.get_account()
        self.positions = {}
        for stock in stock_list:
            self.positions[stock] = None

    def connect_websocket(self):
        self.websocket.run()
        self.websocket.subscribe_trade_updates(self.on_trade_updates)

    def on_trade_updates(self, trade):
        print('trade update', trade)

    def is_market_open(self):
        return self.api.get_clock().is_open

    def get_account(self):
        return self.account

    def get_is_account_blocked(self):
        return self.account.trading_blocked

    def get_buying_power(self):
        return float(self.account.buying_power)

    def get_all_assets(self):
        return self.api.get_assets()

    def get_asset_by_symbol(self, symbol):
        return self.api.get_asset(symbol)

    def get_asset_by_id(self, asset_id):
        return self.api.get_asset_by_id(asset_id)

    def get_orders(self):
        return self.api.get_orders()

    def get_order_by_id(self, order_id):
        return self.api.get_order(order_id)

    async def get_and_store_positions(self):
        while True:
            await asyncio.sleep(5)
            try:
                positions = self.get_positions()
                for position in positions:
                    self.positions[position.symbol] = position
            except Exception as e:
                print('error getting positions', e)

    def get_positions(self):
        return self.api.get_all_positions()

    def get_position_by_symbol(self, symbol):
        return self.api.get_open_position(symbol)

    def close_all_positions(self):
        return self.api.close_all_positions(True)

    def close_position_by_symbol(self, symbol):
        return self.api.close_position(symbol)

    def create_market_order(self, symbol, qty, side, time_in_force, take_profit=None, stop_loss=None):
        return MarketOrderRequest(symbol=symbol, qty=qty, side=side, time_in_force=time_in_force, take_profit=take_profit, stop_loss=stop_loss)

    def create_notional_market_order(self, symbol, notional, side, time_in_force, take_profit=None, stop_loss=None, order_class=OrderClass.SIMPLE):
        return MarketOrderRequest(symbol=symbol, notional=notional, side=side, time_in_force=time_in_force, take_profit=take_profit, stop_loss=stop_loss, order_class=order_class)

    def create_oco_order(self, symbol, qty, time_in_force, take_profit=None, stop_loss=None):
        return LimitOrderRequest(symbol=symbol, qty=qty, side=OrderSide.SELL, time_in_force=time_in_force, take_profit=take_profit, stop_loss=stop_loss, type=OrderClass.OCO)

    def create_limit_order(self, symbol, qty, side, time_in_force, limit_price, take_profit=None, stop_loss=None, order_class=OrderClass.SIMPLE):
        return LimitOrderRequest(symbol=symbol, qty=qty, side=side, time_in_force=time_in_force, limit_price=limit_price, take_profit=take_profit, stop_loss=stop_loss, order_class=order_class)

    def submit_order(self, order):
        return self.api.submit_order(order)

    def on_signal_buy(self, symbol, ask_price, ask_size, limit_price):
        position = None
        if not self.is_market_open():
            print('market is closed')
            return

        [ticker, qty] = calculate_position_size(
            symbol, self.get_buying_power(), .02, 1)
        max_amt_to_buy = round(qty, 0)
        amt_to_buy = min(max_amt_to_buy, ask_size)
        take_profit_price = round(ask_price * 1.01, 2)
        stop_loss_price = round(ask_price * .995, 2)
        take_profit = {'limit_price': take_profit_price}
        stop_loss = {'stop_price': stop_loss_price}

        order = self.create_limit_order(
            symbol, amt_to_buy, OrderSide.BUY, TimeInForce.DAY, round(limit_price, 2), take_profit, stop_loss)
        # Log the order

        return self.submit_order(order)

    def on_signal_sell(self, symbol):
        position = None
        if not self.is_market_open():
            print('market is closed')
            return
        try:
            position = self.get_position_by_symbol(symbol)
        except Exception as e:
            print('error getting position', e)
            return
        if position is None:
            print('no position in', symbol)
            return
        # Log the order

        return self.close_position_by_symbol(symbol)
