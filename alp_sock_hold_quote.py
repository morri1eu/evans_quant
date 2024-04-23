# handle buy decision separately from handling exits
# handle buys on minute bars
# handle exits on quotes
# from alpaca.trading.client import TradingClient
from alpaca.data.live import StockDataStream
from alpaca.trading.enums import OrderSide, TimeInForce
from collections import deque
import numpy as np
import asyncio
from src.paper_trading.alpaca_manager import AlpacaManager
from src.paper_trading.helpers.rsi_crossover_helpers import RSI_Calculator
from src.websockets.eodhd_websocket import EodHd_Websocket
import nest_asyncio
from dotenv import load_dotenv
import os
from src.paper_trading.helpers.bollinger_band_helper import BollingerBandsCalculator
from src.paper_trading.helpers.vwap_helper import VWAPCalculator
nest_asyncio.apply()


class AlpacaWebSocket:
    env = load_dotenv()
    ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
    ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")

    def __init__(self, stock_list):
        self.stock_list = stock_list
        self.alpaca_manager = AlpacaManager(self.stock_list)
        self.rsi_calculators_3 = {stock: RSI_Calculator(3)
                                  for stock in stock_list}
        self.rsi_calculators_14 = {stock: RSI_Calculator(14)
                                   for stock in stock_list}
        self.vwap_calculators = {stock: VWAPCalculator()
                                 for stock in stock_list}

        self.api_key = self.ALPACA_API_KEY
        self.api_secret = self.ALPACA_SECRET_KEY
        self.eodhd_websocket = EodHd_Websocket(
            self.handle_incoming_quote_for_position, self.on_minute_bar)
        self.quotes = {stock: None
                       for stock in stock_list}

    async def connect(self):
        self.conn = StockDataStream(self.api_key, self.api_secret)
        self.eodhd_websocket.connect_quotes(self.stock_list)
        self.eodhd_websocket.connect_trades(self.stock_list)

    # async def log_rsi_for_stock(self, stock):
    #     while True:
    #         await asyncio.sleep(60)  # Wait for 10 seconds
    #         rsi_calculator = self.rsi_calculators.get(stock)
    #         if rsi_calculator:
    #             # Assuming you have a method to get the current RSI
    #             rsi_value = rsi_calculator.current_rsi
    #             print(f"Current RSI for {stock}: {rsi_value}")

    # Create stocks to avoid list when the stock has broken out of the support or resistance hold it in a list for 3 minutes

    def handle_incoming_quote_for_position(self, symbol, quote):
        # print('handling incoming quote', symbol, quote)
        ask_price = float(quote['ask_price'])
        bid_price = float(quote['bid_price'])
        ask_size = int(quote['ask_size'])
        bid_size = int(quote['bid_size'])

        self.quotes[symbol] = [ask_price, ask_size, bid_price, bid_size]
        try:

            current_position = self.alpaca_manager.positions[symbol]

            if current_position is None:
                # print('no position in', symbol)
                return

            current_rsi_3 = self.rsi_calculators_3[symbol].get_rsi()
            current_rsi_14 = self.rsi_calculators_14[symbol].get_rsi()
            current_vwap = self.vwap_calculators.get(symbol).get_vwap()

            print('exit current rsi 3', current_rsi_3)
            print('exit current rsi 14', current_rsi_14)
            print('exit current vwap', current_vwap)

            #     return
            unrealized_plpc = float(current_position.unrealized_plpc)
            entry_price = float(current_position.avg_entry_price)
            qty = int(current_position.qty)

            self.handle_exit_conditions(entry_price, qty, symbol, bid_price, bid_size,
                                        unrealized_plpc, current_rsi_14, current_rsi_3)

            print('no action taken on', symbol)
        except Exception as e:
            print('error handling incoming quote', e)
        return

    def handle_exit_conditions(self, entry_price, qty, symbol, bid_price, bid_size, unrealized_plpc, current_rsi_14, current_rsi_3):
        if entry_price * 1.01 < bid_price and qty > bid_size:
            # Sell the amount of shares that are bid
            limit_order_size = bid_size > qty and qty or bid_size
            print('bid price is higher than take profit, exiting position partially',
                  symbol, bid_price, bid_size)
            self.alpaca_manager.create_limit_order(
                symbol, limit_order_size, OrderSide.SELL, TimeInForce.DAY, bid_price)
            return

        if entry_price * 1.01 < bid_price and qty < bid_size:
            # Sell the amount of shares that are bid
            print('closing position way up',
                  symbol, bid_price, bid_size)
            self.alpaca_manager.close_position_by_symbol(symbol)
            return

        if entry_price * 1.005 < bid_price and qty < bid_size:
            print('bid price is higher than entry price * 1.005 and qty', symbol)
            self.alpaca_manager.close_position_by_symbol(symbol)
            return

        if entry_price * 1.005 < bid_price and qty > bid_size:
            print('bid price is higher than entry price * 1.005 and qty', symbol)
            limit_order_size = bid_size > qty and qty or bid_size
            self.alpaca_manager.create_limit_order(
                symbol, limit_order_size, OrderSide.SELL, TimeInForce.DAY, bid_price)
            return

        if unrealized_plpc > .005 or current_rsi_14 > 70 or current_rsi_3 > 80:
            print('rsi is greater than 70, selling', symbol)
            # for now
            self.alpaca_manager.close_position_by_symbol(symbol)
            return

        if unrealized_plpc < -.05:
            print('stop loss hit', symbol)
            self.alpaca_manager.close_position_by_symbol(symbol)
            return

        print('no action taken on', symbol)
        return

    # async def subscribe_to_stock(self, stock):

        # self.conn.subscribe_updated_bars(self.on_minute_bar, stock)
        # self.conn.subscribe_updated_bars(self.on_minute_bar, stock)
        # print('subscribed to bars', stock)

    def on_minute_bar(self, data):
        print('handling incoming minute bar', data)
        symbol = data.get('m')  # data.S is the symbol
        price = data.get('c')  # data.C is the closing price
        volume = data.get('v')
        self.vwap_calculators.get(symbol).add_tick(price, volume)
        vwap = self.vwap_calculators.get(symbol).get_vwap()
        current_rsi_14 = self.rsi_calculators_14.get(symbol).add_price(price)
        current_rsi_3 = self.rsi_calculators_3.get(symbol).add_price(price)

        print('handling incoming bar', symbol,
              current_rsi_14, current_rsi_3, vwap)
        try:
            current_position = self.alpaca_manager.positions[symbol]
        except Exception as e:
            print('error getting current position', e)

        try:

            ask_price = float(self.quotes.get(symbol)[0])
            bid_price = float(self.quotes.get(symbol)[1])
            ask_size = int(self.quotes.get(symbol)[2])
            bid_size = int(self.quotes.get(symbol)[3])

            print('current rsi 3', current_rsi_3)
            print('current rsi 14', current_rsi_14)
            print('current vwap', vwap)
            if current_position is None and current_rsi_3 is None and current_rsi_14 is None:
                print('no position in', symbol, 'checking if we should buy')
                if current_rsi_14 and current_rsi_14 < 30 and current_rsi_3 < 10:
                    print('rsi_14 is less than 30, and rsi_3 is lees than 10', symbol)
                    if ask_price < vwap:
                        print(
                            'and ask is less than vwap, ', symbol)
                        self.alpaca_manager.on_signal_buy(
                            symbol, ask_price, ask_size, float(ask_price + (vwap - ask_price)/4, 2))
                elif current_rsi_14 and current_rsi_14 < 30 and current_rsi_3 > 10:
                    print(
                        'rsi_14 is less than 30, buying if ask less than vwap', symbol)
                    if ask_price < vwap:
                        print(
                            'ask price is less than vwap, limit buying at ask price', symbol)
                        self.alpaca_manager.on_signal_buy(
                            symbol, ask_price, ask_size, ask_price)
                return
        except Exception as e:
            print('error handling incoming minute bar', e)
            return

    async def run(self):
        try:
            await self.connect()
        except Exception as e:
            print('error connecting', e)
        # # Start the RSI logging task
        asyncio.create_task(self.alpaca_manager.get_and_store_positions())
        for symbol in self.stock_list:
            # asyncio.create_task(self.log_rsi_for_stock(symbol))
            # asyncio.create_task(self.schedule_brackets())
            print('conned')
            # try:
            #     await self.subscribe_to_stock(symbol)
            # except Exception as e:
            #     print('error subscribing', e)
        try:
            await self.conn.run()
        except Exception as e:
            print('error running', e)


# Example usage
stock_list = [
]
# alpaca_manager = AlpacaManager()  # Assuming this is already implemented

websocket = AlpacaWebSocket(stock_list)

asyncio.run(websocket.run())

# schedule a log of rsi_calculators["APPL"] every 5 seconds
# schedule.every(5).seconds.do(lambda: print(
