from src.websockets.eodhd_websocket import EodHd_Websocket
from src.paper_trading.alpaca_manager import AlpacaManager
from alpaca.data.live import StockDataStream
from alpaca.trading.requests import GetAssetsRequest, MarketOrderRequest, LimitOrderRequest, StopOrderRequest, StopLimitOrderRequest, GetOrdersRequest, ClosePositionRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
import asyncio
import schedule


class VWAPTradingStrategy:
    def __init__(self, stock_list):

        self.current_position = {stock:
                                 None for stock in stock_list}  # 'long', 'short', or None
        self.quotes = {stock: None
                       for stock in stock_list}
        self.api_key = self.ALPACA_API_KEY
        self.api_secret = self.ALPACA_SECRET_KEY
        self.alpaca_manager = AlpacaManager(self.stock_list)
        self.eodhd_websocket = EodHd_Websocket(
            self.handle_incoming_quote_for_position)

    # Get and handle bar/quote  strategyupdates

    async def subscribe_to_stock(self, stock):

        self.conn.subscribe_bars(self.on_new_minute_bar, stock)
        # self.conn.subscribe_updated_bars(self.on_price_update, stock)
        print('subscribed to bars', stock)

    def handle_incoming_quote_for_position(self, symbol, quote):
        self.quotes[symbol] = quote
        return

    async def connect(self):
        self.conn = StockDataStream(self.api_key, self.api_secret)
        self.eodhd_websocket.connect_quotes(self.stock_list)

    async def on_new_minute_bar(self, minute_bar):
        """
        Handle a new minute bar.
        :param minute_bar: A dictionary with 'average_price' and 'volume'.
        """
        vwap = minute_bar.vwap
        symbol = minute_bar.symbol
        current_price = minute_bar.close
        current_ask_price = self.quotes[minute_bar.symbol]['ask_price']
        current_bid_price = self.quotes[minute_bar.symbol]['bid_price']

        if vwap is None:
            return  # Not enough data to calculate VWAP

        if current_price > vwap and self.current_position[symbol] != 'long':
            self.enter_long_position(current_ask_price, symbol, vwap)
        elif current_price < vwap and self.current_position[symbol] != 'short':
            self.enter_short_position(current_bid_price, symbol, vwap)

    def enter_long_position(self, entry_price, symbol, vwap):
        print(f"Entering long position at {entry_price}")
        if self.current_position[symbol] == 'short':
            self.alpaca_manager.close_position_by_symbol(symbol)

        notional = self.alpaca_manager.get_buying_power() / 10
        # Implement logic to enter long position
        order = LimitOrderRequest(symbol, notional=notional, side=OrderSide.BUY,
                                  time_in_force=TimeInForce.IOC, limit_price=entry_price, stop_loss={
                                      'stop_price': vwap
                                  })
        self.alpaca_manager.submit_order(order)
        self.current_position[symbol] = 'long'

    def enter_short_position(self, limit_price, symbol, vwap):
        print(f"Entering short position at {limit_price}")
        self.current_position = 'short'
        if self.current_position == 'long':
            self.alpaca_manager.close_position_by_symbol(symbol)
        notional = self.alpaca_manager.get_buying_power() / 10
        order = LimitOrderRequest(symbol, notional=notional, side=OrderSide.SELL,
                                  time_in_force=TimeInForce.IOC, limit_price=limit_price, stop_loss={
                                      'stop_price': vwap
                                  })
        self.alpaca_manager.submit_order(order)
        # Implement logic to enter short position
        self.current_position[symbol] = 'short'

    def check_stop_loss(self, current_price, vwap):
        if self.current_position == 'long' and current_price < vwap:
            print(f"Stop loss triggered for long position at {current_price}")
            self.exit_position()
        elif self.current_position == 'short' and current_price > vwap:
            print(f"Stop loss triggered for short position at {current_price}")
            self.exit_position()

    def exit_position(self):
        print(f"Exiting {self.current_position} position")
        self.current_position = None
        # Implement logic to exit position

    async def run(self):
        try:
            await self.connect()
        except Exception as e:
            print('error connecting strategy', e)
        for stock in self.stock_list:
            try:
                await self.subscribe_to_stock(stock)
                print('connected to ', stock)
            except Exception as e:
                print('error subscribing', e)

        try:
            await self.conn.run()
        except Exception as e:
            print('error running', e)

    async def turn_off(self, stock_list):
        print('exiting positions')
        self.alpaca_manager.close_all_positions()
        print('exited positions')
        print('turning off until tomorrow')
        self.eodhd_websocket.disconnect_quotes()
        self.conn.close()
        self.current_position = {stock:
                                 None for stock in stock_list}  # 'long', 'short', or None
        self.quotes = {stock: None
                       for stock in stock_list}
        print('cache cleared')

    async def schedule_running_algo(self, stock_list):
        while True:
            schedule.every().day.at("08:29").do(self.run, stock_list)
            schedule.every().day.at("14:59").do(self.turn_off, stock_list)
