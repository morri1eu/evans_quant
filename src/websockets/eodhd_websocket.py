import asyncio
import json
import logging
from src.websockets.helpers import get_eodhd_quote_websocket_url, create_quotes_subscription_object, create_crypto_subscription_object
import os
from dotenv import load_dotenv
from src.websockets.json_logger import JSONFormatter
from src.websockets.logger_adapter import LoggerAdapter
from src.websockets.websocket_class.ws_amended import WebSocketClient


name = 'EodHd_Websocket'


class EodHd_Websocket:
    load_dotenv()

    api_key = os.getenv("EOD_HD_API_KEY")

    def __init__(self, handle_incoming_quote_for_position):
        self.websocket_crypto = None
        self.websocket_quotes = None
        self.handle_incoming_quote_for_position = handle_incoming_quote_for_position
        self.on_minute_bar = None

    def connect_crypto(self, crypto_pairs):
        if len(crypto_pairs) == 0:
            print('no crypto pairs to connect to')
            return
        self.websocket_crypto = WebSocketClient(
            api_key=self.api_key,
            endpoint="crypto",
            symbols=crypto_pairs,
            store_data=True,
            display_stream=False,
            display_candle_1m=True,
            display_candle_5m=False,
            display_candle_1h=False,
            quote_callback=self.handle_incoming_quote_for_position,
        )
        try:
            self.websocket_crypto.start()
            print('connected, crypto')
        except Exception as e:
            print('error connecting', e)

    def connect_quotes(self, stock_tickers):
        if len(stock_tickers) == 0:
            print('no stock tickers to connect to')
            return
        self.websocket_quotes = WebSocketClient(
            api_key=self.api_key,
            endpoint="us-quote",
            symbols=stock_tickers,
            store_data=True,
            display_stream=False,
            display_candle_1m=False,
            display_candle_5m=False,
            display_candle_1h=False,
            quote_callback=self.handle_incoming_quote_for_position,
        )
        try:
            print('in connect quotes', self.websocket_quotes.running)
            self.websocket_quotes.start()
            print('connected, quotes')
        except Exception as e:
            print('error connecting', e)

    def connect_trades(self, stock_tickers):
        if len(stock_tickers) == 0:
            print('no stock tickers to connect to')
            return
        self.websocket_quotes = WebSocketClient(
            api_key=self.api_key,
            endpoint="us",
            symbols=stock_tickers,
            store_data=False,
            display_stream=False,
            display_candle_1m=True,
            display_candle_5m=False,
            display_candle_1h=False,
            quote_callback=self.handle_incoming_quote_for_position,
        )
        try:
            print('in connect quotes', self.websocket_quotes.running)
            self.websocket_quotes.start()
            print('connected, quotes')
        except Exception as e:
            print('error connecting', e)

    def disconnect_crypto(self):
        try:
            self.websocket_crypto.stop()
            print('disconnected')
        except Exception as e:
            print('error disconnecting', e)

    def disconnect_quotes(self):
        try:
            self.websocket_quotes.stop()
            print('disconnected')
        except Exception as e:
            print('error disconnecting', e)

    # async def subscribe_to_quotes(self, stock_tickers):
    #     print('in subscribe to quotes', stock_tickers)
    #     subscription = create_quotes_subscription_object(stock_tickers)
    #     params = json.dumps(subscription)
    #     print('params subscribe', params)
    #     response = await self.websocket.send(params)
    #     print('subscribed to quotes', stock_tickers, response)

    # async def handle_message(self):
    #     print('in handle message')
    #     try:
    #         while True:
    #             message = await self.websocket.recv()
    #             message = json.loads(message)
    #             print('message', message['message'])
    #             if message['status_code'] == 200 and not message['message'] == 'Authorized':
    #                 print('in handle message if', message['message'])
    #                 data = message['message']
    #                 self.latest_quotes['s'] = {
    #                     "askPrice": data['ap'],
    #                     "askSize": data['as'],
    #                     "bidPrice": data['bp'],
    #                     "bidSize": data['bs'],
    #                     "timestamp": data['t'],
    #                 }
    #                 print(message)
    #             else:
    #                 print(f"Unhandled message: {message}")
    #     except Exception as e:
    #         self.logger.error(e)

    def run_quotes(self, stock_tickers):
        print('in run quotes', stock_tickers)
        self.connect_quotes()

        # await self.handle_message()

    def get_latest_quote_stock(self, ticker):

        return self.websocket_quotes.get_most_recent_quote(ticker)

    def convert_dollar_values_to_qty(self, ticker, dollar_value):
        print('in convert dollar values to qty', ticker, dollar_value)
        latest_quote = self.get_latest_quote_stock(ticker)
        print('latest quote', latest_quote)
        if latest_quote is None:
            return 0
        # consider slippage
        return dollar_value / latest_quote['askPrice']

    # async def subscribe_to_crypto(self, crypto_tickers):
    #     print('in subscribe to crypto', crypto_tickers)
    #     subscription = create_crypto_subscription_object(crypto_tickers)
    #     params = json.dumps(subscription)
    #     print('params subscribe', params)
    #     response = await self.websocket.send(params)
    #     print('subscribed to crypto', crypto_tickers, response)

    def run_crypto(self, crypto_tickers):
        print('in run crypto', crypto_tickers)
        self.connect_crypto()

    def get_quote_for_stock(self, stock_ticker):
        print('in get quote for stock', stock_ticker)
        all_data = self.websocket_quotes.get_data()
        # await self.handle_message()
