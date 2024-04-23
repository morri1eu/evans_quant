import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import time
import schedule
import pandas as pd
import datetime
import threading
from src.websockets.eodhd_websocket import EodHd_Websocket
from src.paper_trading.alpaca_manager import AlpacaManager
from alpaca.data.live import StockDataStream
from alpaca.trading.models import PositionSide
from alpaca.data.enums import DataFeed
from alpaca.trading.requests import GetAssetsRequest, MarketOrderRequest, LimitOrderRequest, StopOrderRequest, StopLimitOrderRequest, GetOrdersRequest, ClosePositionRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from src.data_fetchers.alpaca.hourly_bars_helper import fetch_hourly_stock_bars_for_rsi_divergence_start_up, fetch_latest_30min_bar
from dotenv import load_dotenv
import os
import nest_asyncio
nest_asyncio.apply()

data_output_path = '../../data/hour/tick_data'


def calculate_rsi(data, window=14, ema=True):
    close_delta = data['close'].diff()
    # Make two series: one for lower closes and one for higher closes
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)

    if ema == True:
        # Use exponential moving average
        ma_up = up.ewm(com=window - 1, adjust=True).mean()
        ma_down = down.ewm(com=window - 1, adjust=True).mean()
    else:
        # Use simple moving average
        ma_up = up.rolling(window=window).mean()
        print(ma_up)
        ma_down = down.rolling(window=window).mean()

    rsi = ma_up / ma_down
    rsi = 100 - (100/(1 + rsi))
    return rsi


class rsi_divergence_trading_strategy:
    env = load_dotenv()
    ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
    ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")

    def __init__(self, stock_list):
        self.stock_list = stock_list
        self.api_key = self.ALPACA_API_KEY
        self.api_secret = self.ALPACA_SECRET_KEY
        self.conn = None
        self.current_position = {stock:
                                 None for stock in self.stock_list}  # 'long', 'short', or None
        self.quotes = {stock: None
                       for stock in self.stock_list}
        self.alpaca_manager = AlpacaManager(self.stock_list)
        self.eodhd_websocket = EodHd_Websocket(
            self.handle_incoming_quote_for_position)
        self.current_hours_minute_bar = {stock: []
                                         for stock in self.stock_list}
        self.dfs = {stock: None for stock in stock_list}

    def handle_incoming_quote_for_position(self, symbol, quote):

        self.quotes[symbol] = quote
        return

    async def connect(self):
        print('connecting to alpaca', self.api_key, self.api_secret)
        self.conn = StockDataStream(
            self.api_key, self.api_secret, feed=DataFeed.SIP)
        print('connecting to quotes')
        self.eodhd_websocket.connect_quotes(self.stock_list)

    async def subscribe_to_stock(self, stock):
        self.conn.subscribe_bars(self.on_new_minute_bar, stock)
        # self.conn.subscribe_updated_bars(self.on_price_update, stock)
        print('subscribed to bars', stock)

    async def on_new_minute_bar(self, minute_bar):
        """
        Handle a new minute bar.
        :param minute_bar: A dictionary with 'average_price' and 'volume'.
        """
        # Get minute bar for each
        print('minute bar', minute_bar)
        print('most recent quote', self.quotes[minute_bar.symbol])
        print('df last row', self.dfs[minute_bar.symbol].iloc[-1])

        # timestamp = minute_bar.t
        # symbol = minute_bar.s
        # open = minute_bar.o
        # high = minute_bar.h
        # low = minute_bar.l
        # close = minute_bar.c
        # volume = minute_bar.v
        # self.current_hours_minute_bar[symbol].append(
        #     {'timestamp': timestamp, 'open': open, 'high': high, 'low': low, 'close': close, 'volume': volume})
        # if len(self.current_hours_minute_bar[symbol]) == 60:
        #     # calculate hourly stats and add to dataframe for each stock then reset current_hours_minute_bar
        #     stocks_df = self.dfs[symbol]
        #     hourly_open = self.current_hours_minute_bar[symbol][0]['open']
        #     hourly_high = max(
        #         [minute['high'] for minute in self.current_hours_minute_bar[symbol]])
        #     hourly_low = min(
        #         [minute['low'] for minute in self.current_hours_minute_bar[symbol]])
        #     hourly_close = self.current_hours_minute_bar[symbol][-1]['close']
        #     hourly_volume = sum(
        #         [minute['volume'] for minute in self.current_hours_minute_bar[symbol]])
        #     # Use datetime and convert to gmt time
        #     timestamp = datetime.time.fromisoformat(
        #         self.current_hours_minute_bar[symbol][-1]['timestamp'])
        #     gmt_offset = 0

        #     stocks_df['rsi'] = calculate_rsi(stocks_df, 5)
        #     stocks_df['rsi_sma'] = stocks_df['rsi'].rolling(window=14).mean()
        #     self.current_hours_minute_bar[symbol].pop(0)

    async def preload(self):
        try:
            for stock in self.stock_list:
                df = fetch_hourly_stock_bars_for_rsi_divergence_start_up(stock)
                self.dfs[stock] = df
                print('last row', self.dfs[stock].iloc[-1])
        except Exception as e:
            print('error preloading', e)

    async def get_hourly_data_for_stock(self, stock):
        try:
            df = fetch_hourly_stock_bars_for_rsi_divergence_start_up(stock)
            self.dfs[stock] = df
            # self.dfs[stock]['timestamp'] = pd.to_datetime(
            #     self.dfs[stock]['timestamp'])
            # self.dfs[stock].set_index('timestamp', inplace=True)
            print('last row', self.dfs[stock].iloc[-1])
        except Exception as e:
            print('error getting hourly data for stock', e)

    async def run(self):
        try:
            await self.connect()
        except Exception as e:
            print('error connecting strategy', e)
            return
        for stock in self.stock_list:
            try:
                if self.dfs[stock] is None:
                    print('no data for', stock)
                    await self.get_hourly_data_for_stock(stock)

            except Exception as e:
                print('error getting hourly data for ', stock, e)
            try:
                await self.subscribe_to_stock(stock)
                print('connected to ', stock)
            except Exception as e:
                print('error subscribing to', stock, e)
        try:
            print('self.conn.run()', self.conn)
            await self.conn.run()
        except Exception as e:
            print('error running', e)

    async def stop(self):
        print('exiting positions')
        self.alpaca_manager.close_all_positions()
        print('exited positions')
        print('turning off until tomorrow')
        self.eodhd_websocket.disconnect_quotes()
        self.conn.close()
        self.current_position = {stock:
                                 None for stock in self.stock_list}  # 'long', 'short', or None
        self.quotes = {stock: None
                       for stock in self.stock_list}
        print('cache cleared')

    async def get_new_30min_bar(self, should_handle_positions=False):
        for stock in self.stock_list:
            try:
                latest_bar = fetch_latest_30min_bar(stock)
                print('latest_bar', latest_bar)
                self.dfs[stock].loc[latest_bar['datetime']] = latest_bar
            except Exception as e:
                print('error getting latest bar', e)
        if should_handle_positions:
            await self.handle_positions_for_rsi_divergence()

    async def handle_long_positions(self, stock, is_current_rsi_20_above_sma, current_position):
        in_long_position = False
        if current_position:
            in_long_position = current_position.side == PositionSide.LONG

        if not in_long_position and is_current_rsi_20_above_sma:
            print('entering long position')
            # May need to exit existing position first
            notional = self.alpaca_manager.get_buying_power() / 20
            if current_position:
                try:
                    self.alpaca_manager.close_position_by_symbol(stock)
                except Exception as e:
                    print('error closing position', e)

            if self.quotes[stock] is None:
                order = MarketOrderRequest(symbol=stock, notional=notional, side=OrderSide.BUY,
                                           time_in_force=TimeInForce.DAY)
                try:
                    self.alpaca_manager.submit_order(order)
                except Exception as e:
                    print('error submitting order', e)
                return
            current_quote = self.quotes[stock]
            current_ask = float(current_quote['askprice'])
            print('current_ask', current_ask)
            order = MarketOrderRequest(symbol=stock, notional=notional, side=OrderSide.BUY,
                                       time_in_force=TimeInForce.DAY, take_profit={'limit_price': current_ask * 1.2}, stop_loss={'stop_price': current_ask * .9})
            try:
                self.alpaca_manager.submit_order(order)
            except Exception as e:
                print('error submitting order', e)

            return

    async def handle_short_positions(self, stock, is_current_rsi_20_below_sma, current_position):
        in_short_position = False
        if current_position:
            in_short_position = current_position.side == PositionSide.SHORT

        if not in_short_position and is_current_rsi_20_below_sma:
            print('entering short position')
            # May need to exit existing position first
            notional = self.alpaca_manager.get_buying_power() / 20
            current_quote = self.quotes[stock]
            current_bid = float(current_quote['bid_price'])
            qty = int(notional / current_bid)
            if current_position:
                try:
                    self.alpaca_manager.close_position_by_symbol(stock)
                except Exception as e:
                    print('error closing position', e)

            if self.quotes[stock] is None:
                order = MarketOrderRequest(symbol=stock, notional=notional, side=OrderSide.SELL,
                                           time_in_force=TimeInForce.DAY)
                try:
                    self.alpaca_manager.submit_order(order)
                except Exception as e:
                    print('error submitting order', e)
                return
            print('current_bid', current_bid)
            order = MarketOrderRequest(symbol=stock, qty=qty, side=OrderSide.SELL,
                                       time_in_force=TimeInForce.DAY, take_profit={'limit_price': current_bid * .8}, stop_loss={'stop_price': current_bid * 1.1})
            try:
                self.alpaca_manager.submit_order(order)
            except Exception as e:
                print('error submitting order', e)

            return

        if in_short_position and is_current_rsi_20_below_sma:
            print('short position still valid')
            return

    async def handle_positions_for_rsi_divergence(self):
        for stock in self.stock_list:
            print('handling positions for', stock)
            if self.dfs[stock] is None:
                continue
            df = self.dfs[stock]
            # doubling the window to 10 because we are using 30 min bars
            df['rsi'] = calculate_rsi(df, 10)
            # doubling the window to 28 because we are using 30 min bars
            df['rsi_sma'] = df['rsi'].rolling(window=28).mean()
            current_rsi = df.iloc[-1]['rsi']
            current_rsi_sma = df.iloc[-1]['rsi_sma']
            short_threshold = current_rsi_sma - 20
            long_threshold = current_rsi_sma + 20
            is_current_rsi_20_below_sma = current_rsi < short_threshold  # Short Signal
            is_current_rsi_20_above_sma = current_rsi > long_threshold  # Long Signal
            print('long_signal', is_current_rsi_20_above_sma)
            print('short_signal', is_current_rsi_20_below_sma)
            try:
                current_position = self.alpaca_manager.get_position_by_symbol(
                    stock)
            except Exception as e:
                print('error getting position', e)
                current_position = None
            try:
                await self.handle_long_positions(
                    stock, is_current_rsi_20_above_sma, current_position)
                await self.handle_short_positions(
                    stock, is_current_rsi_20_below_sma, current_position)
            except Exception as e:
                print('error handling positions', e)

    async def schedule_running_algo(self):
        scheduler = AsyncIOScheduler()
        scheduler.add_job(self.preload, CronTrigger(hour=8, minute=17))
        scheduler.add_job(self.run, CronTrigger(hour=8, minute=29))
        scheduler.add_job(self.stop, CronTrigger(hour=14, minute=59))
        scheduler.add_job(self.get_new_30min_bar,
                          CronTrigger(minute='30'), args=[True])
        scheduler.add_job(self.get_new_30min_bar,
                          CronTrigger(minute='00'), args=[True])

        scheduler.start()
        if self.conn is None:
            await self.run()

        try:
            # Keep the program running
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            pass

    # def run_scheduler(self):
    #     while True:x
    #         schedule.run_pending()
    #         time.sleep(1)


stock_list = [
]

websocket = rsi_divergence_trading_strategy(stock_list)

asyncio.run(websocket.schedule_running_algo())
