import time
import schedule
import json
from datetime import datetime, timedelta
from src.paper_trading.alpaca_manager import AlpacaManager
from src.paper_trading.get_signals import get_signals_for_exchange
from src.paper_trading.position_sizing import calculate_position_sizes
from dotenv import load_dotenv
import pandas as pd
import os
from src.paper_trading.order_templating import get_orders_from_position_sizes
from alpaca.trading.enums import OrderSide, TimeInForce
from src.websockets.eodhd_websocket import EodHd_Websocket

MAX_DECIMALS = 2


class TradingServer:
    # Initialize the AlpacaManager with your API keys
    alpaca_manager = AlpacaManager()

    eodhd_websocket = EodHd_Websocket()

    def connect_websockets(self, stock_tickers, crypto_pairs):
        self.eodhd_websocket.connect_crypto(crypto_pairs)
        self.eodhd_websocket.connect_quotes(stock_tickers)

    def get_most_recent_quote_for_stock(self, stock_ticker):
        return self.eodhd_websocket.websocket_quotes.get_most_recent_quote(stock_ticker)

    def log_to_file(file_path, data):
        with open(file_path, 'a') as file:
            json.dump(data, file)
            file.write('\n')

    def prepare_trading_strategy(self):
        exchange = 'NYSE'
        # if not alpaca_manager.is_market_open():
        #     print("Market is not open. Preparing for the next market open...")
        #     return

        # Generate signals for each stock in your universe
        [long_signals, short_signals] = get_signals_for_exchange(
            exchange=exchange, alpha_name='alpha_1')
        print('signals')

        # Get Parameters for sizing
        buying_power = self.alpaca_manager.get_buying_power()
        print('buying power', buying_power)
        risk_per_trade = 0.02  # 2% risk per trade
        stop_loss_percent = 1 - 0.05  # 5% stop loss

        # Calculate position sizes
        long_positions = calculate_position_sizes(
            long_signals, buying_power, risk_per_trade, stop_loss_percent)
        print('positions')

        long_orders = get_orders_from_position_sizes(long_positions)
        print(long_orders)
        # Prepare orders and log them
        long_orders.to_csv(
            f'../logs/prepared_orders/{exchange}/long/{datetime.now().strftime("%Y-%m-%d")}.csv')
        self.connect_websockets(long_orders['Stock'], [])

        short_positions = calculate_position_sizes(
            short_signals, buying_power, risk_per_trade, stop_loss_percent)
        short_orders = get_orders_from_position_sizes(short_positions)
        short_orders.to_csv(
            f'../logs/prepared_orders/{exchange}/short/{datetime.now().strftime("%Y-%m-%d")}.csv')
        self.connect_websockets(short_orders['Stock'], [])
        # print('prepared orders')
        # Save the prepared orders to be executed at market open
        # with open('prepared_orders.json', 'w') as file:
        #     json.dump(prepared_orders, file)

    def execute_prepared_orders(self):
        exchange = 'NYSE'
        # self.alpaca_manager.connect_websocket()
        # Load the prepared orders
        long_prepared_orders = pd.read_csv(
            f'../logs/prepared_orders/{exchange}/long/{datetime.now().strftime("%Y-%m-%d")}.csv')

        short_prepared_orders = pd.read_csv(
            f'../logs/prepared_orders/{exchange}/short/{datetime.now().strftime("%Y-%m-%d")}.csv')

        submitted_orders = []
        # # Execute trades and log them
        for [index, data] in long_prepared_orders.iterrows():
            # qty = self.eodhd_websocket.convert_dollar_values_to_qty(
            #     ticker, dollar_value)
            # Get the price of the stock from websocket
            ticker = data['Stock']
            dollar_value = round(data['Size'], 2)
            print('ticker', ticker)
            print('dollar value', dollar_value)
            try:
                order_to_send = self.alpaca_manager.create_notional_market_order(
                    ticker, dollar_value, OrderSide.BUY, TimeInForce.DAY)
                submitted_order = self.alpaca_manager.submit_order(
                    order_to_send)
                submitted_orders.append(submitted_order)
                print(submitted_order)
            except Exception as e:
                print('Order submission failed', e)
        submitted_orders_df = pd.DataFrame(submitted_orders)
        submitted_orders_df.to_csv(
            f'../logs/submitted_orders/{exchange}/long/{datetime.now().strftime("%Y-%m-%d")}.csv')

        # short_submitted_orders = []
        # for [index, data] in short_prepared_orders.iterrows():
        #     # qty = self.eodhd_websocket.convert_dollar_values_to_qty(
        #     #     ticker, dollar_value)
        #     # Get the price of the stock from websocket
        #     ticker = data['Stock']
        #     dollar_value = round(data['Size'], 2)
        #     print('ticker', ticker)
        #     print('dollar value', dollar_value)
        #     amt = self.eodhd_websocket.convert_dollar_values_to_qty(
        #         ticker, dollar_value).__floor__()
        #     try:
        #         order_to_send = self.alpaca_manager.create_market_order(
        #             ticker, amt, OrderSide.SELL, TimeInForce.DAY)
        #         submitted_order = self.alpaca_manager.submit_order(
        #             order_to_send)
        #         submitted_orders.append(submitted_order)
        #         print(submitted_order)
        #     except Exception as e:
        #         print('Order submission failed', e)
        # short_submitted_orders = pd.DataFrame(submitted_orders)
        # short_submitted_orders.to_csv(
        #     f'../logs/submitted_orders/{exchange}/short/{datetime.now().strftime("%Y-%m-%d")}.csv')

    def close_positions(self):
        self.alpaca_manager.close_all_positions()

    def run_server(self):
        # Schedule the trading strategy preparation to run before market open
        schedule.every().day.at("05:30").do(self.prepare_trading_strategy)

        # Schedule the order execution to run at market open
        schedule.every().day.at("06:00").do(self.execute_prepared_orders)

        # Schedule the closing function to run 15 minutes before market close
        schedule.every().day.at("14:45").do(self.alpaca_manager.close_all_positions)

        while True:
            schedule.run_pending()
            time.sleep(1)

    # if __name__ == "__main__":
    #     run_server()
