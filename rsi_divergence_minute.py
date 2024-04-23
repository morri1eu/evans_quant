import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import time
import schedule
import polars as pl
import pandas as pd
import datetime
import threading
from src.websockets.eodhd_websocket import EodHd_Websocket
from src.paper_trading.alpaca_manager import AlpacaManager
from alpaca.data.live import StockDataStream
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.models import PositionSide
from alpaca.data.enums import DataFeed
from alpaca.trading.requests import GetAssetsRequest, MarketOrderRequest
from alpaca.data.requests import StockLatestTradeRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from src.data_fetchers.alpaca.hourly_bars_helper import fetch_minute_stock_bars_for_rsi_divergence_start_up, fetch_latest_30min_bar
from dotenv import load_dotenv
import os
import nest_asyncio
nest_asyncio.apply()

data_output_path = '../../data/hour/tick_data'


def calculate_rsi(data, window=14, ema=True):
    close_delta = data['close'].diff()
    # Make two series: one for lower closes and one for higher closes
    up = close_delta.clip(lower_bound=0)
    down = -1 * close_delta.clip(upper_bound=0)

    if ema == True:
        # Use exponential moving average
        ma_up = up.ewm_mean(com=window - 1, adjust=True)
        ma_down = down.ewm_mean(com=window - 1, adjust=True)
    else:
        # Use simple moving average
        ma_up = up.rolling_mean(window_size=window)

        ma_down = down.rolling_mean(window_size=window)

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

        # self.quotes = {stock: None
        #                for stock in self.stock_list}
        self.alpaca_manager = AlpacaManager(self.stock_list)

        self.dfs = {stock: None for stock in stock_list}

    # def handle_incoming_quote_for_position(self, symbol, quote):
    #     self.quotes[symbol] = quote
    #     return

    async def connect(self):
        print('connecting to alpaca', self.api_key, self.api_secret)
        self.conn = StockDataStream(
            self.api_key, self.api_secret, feed=DataFeed.SIP)
        self.data_api = StockHistoricalDataClient(
            self.api_key, self.api_secret)

    async def subscribe_to_stock(self, stock):
        self.conn.subscribe_bars(self.on_new_minute_bar, stock)
        # self.conn.subscribe_quotes(
        #     self.handle_incoming_quote_for_position, stock)
        print('subscribed to bars', stock)

    async def on_new_minute_bar(self, minute_bar):
        """
        Handle a new minute bar.
        :param minute_bar: A dictionary with 'average_price' and 'volume'.
        """
        # Get minute bar for each
        stock = minute_bar.symbol
        high = minute_bar.high
        low = minute_bar.low
        close = minute_bar.close
        volume = minute_bar.volume
        timestamp = minute_bar.timestamp
        vwap = minute_bar.vwap
        trade_count = minute_bar.trade_count
        open = minute_bar.open
        symbol = minute_bar.symbol

        data_to_append = {
            'symbol': stock,
            'open': open,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
            'datetime': pd.to_datetime(timestamp),
            'trade_count': trade_count,
            'vwap': vwap,
        }

        df = pd.DataFrame(data_to_append, index=['datetime'])

        df.drop(columns=['datetime'], inplace=True)
        pl_df = pl.from_pandas(df)

        pl.concat([self.dfs[stock], pl_df])

        await self.handle_positions_for_rsi_divergence(symbol)

    async def preload(self):
        try:
            for stock in self.stock_list:
                df = fetch_minute_stock_bars_for_rsi_divergence_start_up(stock)
                self.dfs[stock] = df
                print('last row', self.dfs[stock])
        except Exception as e:
            print('error preloading', e)

    async def get_minute_data_for_stock(self, stock):
        try:
            df = fetch_minute_stock_bars_for_rsi_divergence_start_up(stock)
            self.dfs[stock] = df
            # self.dfs[stock]['timestamp'] = pd.to_datetime(
            #     self.dfs[stock]['timestamp'])
            # self.dfs[stock].set_index('timestamp', inplace=True)
            print('last row', self.dfs[stock])
        except Exception as e:
            print('error getting minute data for stock', e)

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
                    await self.get_minute_data_for_stock(stock)

            except Exception as e:
                print('error getting minute data for ', stock, e)
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
        self.conn.close()
        self.current_position = {stock:
                                 None for stock in self.stock_list}  # 'long', 'short', or None
        self.quotes = {stock: None
                       for stock in self.stock_list}
        print('cache cleared')

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

            current_price = self.get_current_price(stock)

            qty = int(notional / current_price)

            order = MarketOrderRequest(symbol=stock, qty=qty, side=OrderSide.BUY, order_class=OrderClass.BRACKET,
                                       time_in_force=TimeInForce.DAY, take_profit={'limit_price': round(current_price * 1.003, 2)}, stop_loss={'stop_price': round(current_price * .9985, 2)})
            try:
                self.alpaca_manager.submit_order(order)
            except Exception as e:
                print('error submitting order', e)

            return

    def get_current_price(self, stock):
        latest_trade_request = StockLatestTradeRequest(
            symbol_or_symbols=stock, feed=DataFeed.SIP)
        latest_trade = self.data_api.get_stock_latest_trade(
            latest_trade_request)
        print('latest_trade', latest_trade[stock].price)
        current_price = float(latest_trade[stock].price)
        return current_price

    async def handle_short_positions(self, stock, is_current_rsi_20_below_sma, current_position):
        in_short_position = False
        if current_position:
            in_short_position = current_position.side == PositionSide.SHORT

        if not in_short_position and is_current_rsi_20_below_sma:
            print('entering short position')
            # May need to exit existing position first
            notional = self.alpaca_manager.get_buying_power() / 20

            current_price = self.get_current_price(stock)
            qty = int(notional / current_price)

            if current_position:
                try:
                    self.alpaca_manager.close_position_by_symbol(stock)
                except Exception as e:
                    print('error closing position', e)

            order = MarketOrderRequest(symbol=stock, qty=qty, side=OrderSide.SELL, order_class=OrderClass.BRACKET,
                                       time_in_force=TimeInForce.DAY, take_profit={'limit_price': round(current_price * .997, 2)}, stop_loss={'stop_price': round(current_price * 1.0015, 2)})
            try:
                self.alpaca_manager.submit_order(order)
            except Exception as e:
                print('error submitting order', e)

            return

        if in_short_position and is_current_rsi_20_below_sma:
            print('short position still valid')
            return

    async def handle_positions_for_rsi_divergence(self, stock):
        print('handling positions for', stock)
        if self.dfs[stock] is None:
            return
        df = self.dfs[stock]
        rsi = calculate_rsi(df, 5)
        df_with_rsi = df.with_columns(
            pl.Series(name='rsi', values=rsi))

        # df['rsi_sma'] = df['rsi'].rolling(window=14).mean()

        df_with_rsi_sma = df_with_rsi.with_columns(pl.Series(name='rsi_sma', values=df_with_rsi['rsi'].rolling_mean(
            window_size=14)))

        current_rsi = df_with_rsi_sma.tail(1)['rsi']
        current_rsi_sma = df_with_rsi_sma.tail(1)['rsi_sma']

        print('current_rsi', current_rsi_sma.tail(1))

        short_threshold = current_rsi_sma - 20
        long_threshold = current_rsi_sma + 20

        is_current_rsi_20_below_sma = current_rsi < short_threshold  # Short Signal
        is_current_rsi_20_above_sma = current_rsi > long_threshold  # Long Signal

        print('long_signal', is_current_rsi_20_above_sma[0])
        print('short_signal', is_current_rsi_20_below_sma[0])

        is_market_open = self.alpaca_manager.is_market_open()

        if is_market_open:

            try:
                current_position = self.alpaca_manager.get_position_by_symbol(
                    stock)
            except Exception as e:
                print('error getting position', e)
                current_position = None
            try:
                await self.handle_long_positions(
                    stock, is_current_rsi_20_above_sma[0], current_position)
                await self.handle_short_positions(
                    stock, is_current_rsi_20_below_sma[0], current_position)
            except Exception as e:
                print('error handling positions', e)
                return
        else:
            print('market is closed')

    async def schedule_running_algo(self):
        scheduler = AsyncIOScheduler()
        scheduler.add_job(self.preload, CronTrigger(hour=8, minute=17))
        scheduler.add_job(self.run, CronTrigger(hour=8, minute=29))
        scheduler.add_job(self.stop, CronTrigger(hour=14, minute=45))
        # scheduler.add_job(self.get_new_30min_bar,
        #                   CronTrigger(minute='30'), args=[True])
        # scheduler.add_job(self.get_new_30min_bar,
        #                   CronTrigger(minute='00'), args=[True])

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
