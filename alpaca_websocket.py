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


# make exit check evcery 20 seconds
# if we've been in position for more than 5 minutes and losing more than .5% exit
# if we've been in position for more than 5 minutes and winning more than 1% exit
# if we've made 20 dollars exit
# if we've lost 5 dollars exit


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
        self.vwap = {stock: None
                     for stock in stock_list}
        self.api_key = self.ALPACA_API_KEY
        self.api_secret = self.ALPACA_SECRET_KEY
        self.eodhd_websocket = EodHd_Websocket(
            self.handle_incoming_quote_for_position)
        self.quotes = {stock: None
                       for stock in stock_list}

    async def connect(self):
        self.conn = StockDataStream(self.api_key, self.api_secret)
        self.eodhd_websocket.connect_quotes(self.stock_list)

    async def log_rsi_for_stock(self, stock):
        while True:
            await asyncio.sleep(60)  # Wait for 10 seconds
            rsi_calculator = self.rsi_calculators_3.get(stock)
            if rsi_calculator:
                # Assuming you have a method to get the current RSI
                rsi_value = rsi_calculator.get_rsi()
                print(f"Current RSI for {stock}: {rsi_value}")

    # Create stocks to avoid list when the stock has broken out of the support or resistance hold it in a list for 3 minutes
    async def handle_exiting_positions_poll(self, symbol):
        while True:
            await asyncio.sleep(20)
            try:

                position = self.alpaca_manager.get_position_by_symbol(symbol)
                print('position', position)
                if position is None:
                    return

                quote = self.quotes[symbol]
                bid_price = float(quote['bid_price'])
                bid_size = int(quote['bid_size'])

                current_rsi_3 = self.rsi_calculators_3[symbol].get_rsi()
                current_rsi_14 = self.rsi_calculators_14[symbol].get_rsi()
                current_vwap = self.vwap.get(symbol)

                unrealized_plpc = float(position.unrealized_plpc)
                unrealized_pl = float(position.unrealized_pl)
                entry_price = float(position.avg_entry_price)
                market_value = float(position.market_value)

                qty = int(position.qty)

                print('handling exiting positions poll', symbol, bid_price, bid_size, current_rsi_3,
                      current_rsi_14, current_vwap, unrealized_plpc, unrealized_pl, entry_price, qty, market_value)

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
                    print(
                        'bid price is higher than entry price * 1.005 and qty', symbol)
                    self.alpaca_manager.close_position_by_symbol(symbol)
                    return

                if entry_price * 1.005 < bid_price and qty > bid_size:
                    print(
                        'bid price is higher than entry price * 1.005 and qty', symbol)
                    limit_order_size = bid_size > qty and qty or bid_size
                    self.alpaca_manager.create_limit_order(
                        symbol, limit_order_size, OrderSide.SELL, TimeInForce.DAY, bid_price)
                    return

                if unrealized_plpc > .005:
                    print('rsi is greater than 70, selling', symbol)
                    # for now
                    self.alpaca_manager.close_position_by_symbol(symbol)
                    return

                if unrealized_plpc < -.05:
                    print('stop loss hit', symbol)
                    self.alpaca_manager.close_position_by_symbol(symbol)
                    return

                if unrealized_pl > 15 and market_value < 2500:
                    print('unrealized pl is greater than 15 selling', symbol)
                    self.alpaca_manager.close_position_by_symbol(symbol)
                    return

                if unrealized_pl < -10 < market_value:
                    print('has lost 10 dollars sell', symbol)
                    self.alpaca_manager.close_position_by_symbol(symbol)
                    return

                if current_rsi_14 > 70 or current_rsi_3 > 80:
                    print('rsi is greater than 70, selling', symbol)
                    # for now
                    self.alpaca_manager.close_position_by_symbol(symbol)
                    return

            except Exception as e:
                print('error handling exiting positions poll', e)

    def handle_incoming_quote_for_position(self, symbol, quote):
        self.quotes[symbol] = quote
        return

    # def handle_exit_conditions(self, entry_price, qty, symbol, bid_price, bid_size, unrealized_plpc, current_rsi_14, current_rsi_3):
    #     if entry_price * 1.01 < bid_price and qty > bid_size:
    #         # Sell the amount of shares that are bid
    #         limit_order_size = bid_size > qty and qty or bid_size
    #         print('bid price is higher than take profit, exiting position partially',
    #               symbol, bid_price, bid_size)
    #         self.alpaca_manager.create_limit_order(
    #             symbol, limit_order_size, OrderSide.SELL, TimeInForce.DAY, bid_price)
    #         return

    #     if entry_price * 1.01 < bid_price and qty < bid_size:
    #         # Sell the amount of shares that are bid
    #         print('closing position way up',
    #               symbol, bid_price, bid_size)
    #         self.alpaca_manager.close_position_by_symbol(symbol)
    #         return

    #     if entry_price * 1.005 < bid_price and qty < bid_size:
    #         print('bid price is higher than entry price * 1.005 and qty', symbol)
    #         self.alpaca_manager.close_position_by_symbol(symbol)
    #         return

    #     if entry_price * 1.005 < bid_price and qty > bid_size:
    #         print('bid price is higher than entry price * 1.005 and qty', symbol)
    #         limit_order_size = bid_size > qty and qty or bid_size
    #         self.alpaca_manager.create_limit_order(
    #             symbol, limit_order_size, OrderSide.SELL, TimeInForce.DAY, bid_price)
    #         return

    #     if unrealized_plpc > .005 or current_rsi_14 > 70 or current_rsi_3 > 80:
    #         print('rsi is greater than 70, selling', symbol)
    #         # for now
    #         self.alpaca_manager.close_position_by_symbol(symbol)
    #         return

    #     if unrealized_plpc < -.05:
    #         print('stop loss hit', symbol)
    #         self.alpaca_manager.close_position_by_symbol(symbol)
    #         return

    #     print('no action taken on', symbol)
    #     return

    async def subscribe_to_stock(self, stock):

        self.conn.subscribe_bars(self.on_price_update, stock)
        # self.conn.subscribe_updated_bars(self.on_price_update, stock)
        print('subscribed to bars', stock)

    async def on_price_update(self, data):
        print('handling incoming bar', data)
        symbol = data.symbol  # data.S is the symbol
        price = data.close  # data.C is the closing price
        vwap = data.vwap
        self.vwap[symbol] = vwap

        current_rsi_3 = self.rsi_calculators_3.get(symbol).add_price(price)
        current_rsi_14 = self.rsi_calculators_14.get(symbol).add_price(price)
        current_vwap = self.vwap.get(symbol)

        print('current rsi 3', current_rsi_3)
        print('current rsi 14', current_rsi_14)
        print('current vwap', current_vwap)
        try:
            ask_price = float(self.quotes[symbol]['ask_price'])
            ask_size = int(self.quotes[symbol]['ask_size'])
        except Exception as e:
            print('error getting ask price and size', e)
            return
        try:
            if not current_rsi_3 is None and not current_rsi_14 is None:
                print('no position in', symbol, 'checking if we should buy')
                if current_rsi_14 and current_rsi_14 < 30 and current_rsi_3 < 10:
                    print('rsi_14 is less than 30, and rsi_3 is lees than 10', symbol)
                    # short on the opposite current rsi 14
                    print(
                        'and ask is less than current_vwap, ', symbol, ask_price, )
                    self.alpaca_manager.on_signal_buy(
                        symbol, ask_price, ask_size, round(vwap, 2))
                elif current_rsi_14 and current_rsi_14 < 30 and current_rsi_3 > 10:
                    print(
                        'rsi_14 is less than 30, buying if ask less than vwap', symbol)
                    if ask_price < vwap:
                        print(
                            'ask price is less than vwap, limit buying at ask price', symbol)
                        self.alpaca_manager.on_signal_buy(
                            symbol, ask_price, ask_size, vwap)
                return
        except Exception as e:
            print('error in logic opening position', e)

    async def run(self):
        try:
            await self.connect()
        except Exception as e:
            print('error connecting', e)
        # # Start the RSI logging task
        for symbol in self.stock_list:
            # asyncio.create_task(self.log_rsi_for_stock(symbol))
            asyncio.create_task(self.handle_exiting_positions_poll(symbol))

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
    'COST',
    'AAL',
    'KHC',
    'MAT',
    'SIRI',
    'WBA',
    'NCLH',
    'VOD',
    'ADSK',
    'TMUS',
    'ATVI',
    'AVGO',
    'GILD',
    'EBAY',
    'EXPE',
    'VRTX',
    'BIDU',
    'PYPL',
    'MCHP',
    'SWKS',
    'JD',
    'MU',
    'NXPI',
    'AMAT',
    'WDC',
    'CSX',
    'TRIP',
    'TSCO',
    'FAST',
    'LRCX'
]
# alpaca_manager = AlpacaManager()  # Assuming this is already implemented

websocket = AlpacaWebSocket(stock_list)

asyncio.run(websocket.run())

# schedule a log of rsi_calculators["APPL"] every 5 seconds
# schedule.every(5).seconds.do(lambda: print(
