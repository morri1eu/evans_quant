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

        self.rsi_calculators_50 = {stock: RSI_Calculator(10)
                                   for stock in stock_list}
        self.rsi_calculators_250 = {stock: RSI_Calculator(50)
                                    for stock in stock_list}
        # self.vwap = {stock: None
        #              for stock in stock_list}

        self.api_key = self.ALPACA_API_KEY
        self.api_secret = self.ALPACA_SECRET_KEY
        self.eodhd_websocket = EodHd_Websocket(
            self.handle_incoming_quote_for_position)

        self.current_prices = {stock: None for stock in stock_list}

        self.num_of_trades_for_stock = {stock: 0 for stock in stock_list}

    async def connect(self):
        self.conn = StockDataStream(self.api_key, self.api_secret)
        self.eodhd_websocket.connect_quotes(self.stock_list)

    # async def schedule_brackets(self):
    #     while True:
    #         await asyncio.sleep(60)
    #         print('checking open positions')
    #         try:
    #             positions = self.alpaca_manager.get_positions()
    #             for position in positions:
    #                 print('checking position', position.symbol)
    #                 entry_price = position.avg_entry_price
    #                 take_profit_price = round(
    #                     float(entry_price) * 1.005, 2)
    #                 stop_loss_price = round(float(entry_price) * .998, 2)
    #                 current_price = float(position.current_price)
    #                 if (current_price > take_profit_price):
    #                     print('price is higher than take profit exiting',
    #                           position.symbol, 'Profit', position.unrealized_pl)
    #                     self.alpaca_manager.close_position_by_symbol(
    #                         position.symbol)

    #                 elif (current_price < stop_loss_price):
    #                     print('price is lower than stop loss exiting',
    #                           position.symbol, 'Loss', position.unrealized_pl)
    #                     self.alpaca_manager.close_position_by_symbol(
    #                         position.symbol)

    #                 print('no action taken on', position.symbol)

    #         except Exception as e:
    #             print('error handling open positions', e)
    #             return

    # Create stocks to avoid list when the stock has broken out of the support or resistance hold it in a list for 3 minutes

    def handle_incoming_quote_for_position(self, symbol, quote):
        print('handling incoming quote', symbol, quote)

        ask_price = float(quote['ask_price'])
        bid_price = float(quote['bid_price'])
        ask_size = int(quote['ask_size'])
        bid_size = int(quote['bid_size'])

        try:
            current_position = self.alpaca_manager.positions[symbol]
            print('current position', symbol, current_position)

            # deviation_percent = deviation_amount / current_moving_average
            # use deviation percentage instead of flat percentage in take profit and stop loss
            # Limit size of buys if deviation percent is too low

            current_rsi_50 = self.rsi_calculators_50[symbol].current_rsi
            current_rsi_250 = self.rsi_calculators_250[symbol].current_rsi

            print('current_rsi_50', symbol, current_rsi_50)
            print('current_rsi_250', symbol, current_rsi_250)
            if current_position is None:  # and limit_price
                print('no position in', symbol, 'checking if we should buy')
                if current_rsi_250 and current_rsi_250 < 30 and current_rsi_50 and current_rsi_50 < 10:
                    # limit_price = self.calculate_deviation_values(
                    #     current_support, current_resistance, current_moving_average, ask_price)
                    # print('limit price', limit_price)
                    print('rsi is less than 30, buying', symbol)
                    self.alpaca_manager.on_signal_buy(
                        symbol, ask_price, ask_size)  # round(ask_price * 1.001, 2)
                return

            if current_position is None:
                return

            unrealized_plpc = float(current_position.unrealized_plpc)
            entry_price = float(current_position.avg_entry_price)
            qty = int(current_position.qty)

            self.handle_exit_conditions(
                entry_price, qty, symbol, bid_price, bid_size, unrealized_plpc, current_rsi_250, current_rsi_50)

        except Exception as e:
            print('error handling incoming quote', e)
        return

    def handle_exit_conditions(self, entry_price, qty, symbol, bid_price, bid_size, unrealized_plpc, current_rsi_250, current_rsi_50):
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

        if unrealized_plpc > .005 or current_rsi_250 > 70 or current_rsi_50 > 80:
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

    def calculate_deviation_values(current_support, current_resistance, current_moving_average, ask_price):
        deviation_amount = current_resistance - current_moving_average
        # deviation_percent = deviation_amount / current_moving_average
        # use deviation percentage instead of flat percentage in take profit and stop loss
        # Limit size of buys if deviation percent is too low
        is_valid_entry_price_support = (
            ask_price > current_support and ask_price < current_support + (deviation_amount * .3))
        is_valid_entry_price_resistance = (
            ask_price > current_moving_average and ask_price < current_resistance - (deviation_amount * .7))

        if not is_valid_entry_price_support and not is_valid_entry_price_resistance:
            return None

        limit_price = is_valid_entry_price_support and current_support + \
            (deviation_amount * .3) or is_valid_entry_price_resistance and current_resistance - \
            (deviation_amount * .7)

        return limit_price

    async def subscribe_to_stock(self, stock):

        self.conn.subscribe_trades(self.on_trade, stock)
        # self.conn.subscribe_updated_bars(self.on_trade, stock)
        print('subscribed to bars', stock)

    async def on_trade(self, data):
        symbol = data.symbol  # data.S is the symbol
        price = data.price  # data.C is the closing price

        print('on trade', symbol, price)
        self.rsi_calculators_50[symbol].add_price(price)
        self.rsi_calculators_250[symbol].add_price(price)

        self.current_prices[symbol] = price

        self.num_of_trades_for_stock[symbol] += 1
        print('num of trades for stock', symbol,
              self.num_of_trades_for_stock[symbol])

    async def run(self):
        try:
            await self.connect()
        except Exception as e:
            print('error connecting', e)
        # # Start the RSI logging task
        for symbol in self.stock_list:
            # asyncio.create_task(self.schedule_brackets())
            asyncio.create_task(self.alpaca_manager.get_and_store_positions())
            print('conned')
            try:
                await self.subscribe_to_stock(symbol)
            except Exception as e:
                print('error subscribing', e)
        try:
            await self.conn.run()
        except Exception as e:
            print('error running', e)


# Example usage
stock_list = [
    'TMUS',
    'AAL',
    'KHC']
# alpaca_manager = AlpacaManager()  # Assuming this is already implemented

websocket = AlpacaWebSocket(stock_list)

asyncio.run(websocket.run())

# schedule a log of rsi_calculators["APPL"] every 5 seconds
# schedule.every(5).seconds.do(lambda: print(
