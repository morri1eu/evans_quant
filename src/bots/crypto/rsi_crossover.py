
# from alpaca_trade_api.rest import TimeFrame
import time
import numpy as np
import pandas as pd

# from get_data import Get_Data
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.trading.enums import OrderSide, TimeInForce

import datetime as dt
import os
from dotenv import load_dotenv


class Crypto_RSI_Crossover_Bot:
    env = load_dotenv()
    ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
    ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")

    def __init__(self):
        # alp_base_url = 'https://paper-api.alpaca.markets'
        api = TradingClient(self.ALPACA_API_KEY,
                            self.ALPACA_SECRET_KEY)

        self.data_url = 'https://data.alpaca.markets/v1beta1/crypto'
        self.header = {
            'APCA-API-KEY-ID': self.ALPACA_API_KEY,
            'APCA-API-SECRET-KEY': self.ALPACA_SECRET_KEY}

        self.api_key = self.ALPACA_API_KEY
        self.secret_key = self.ALPACA_SECRET_KEY
        self.api = api
        self.crypto_client = CryptoHistoricalDataClient()
        self.account = self.api.get_account()

    # calculate ema crossovers
    def calculate_cross_over(self, df):
        df['9_EMA'] = df['close'].ewm(span=9).mean()
        df['21_EMA'] = df['close'].ewm(span=21).mean()
        df['golden_cross'] = np.where(df['9_EMA'] > df['21_EMA'], 1, 0)
        df['death_cross'] = np.where(df['21_EMA'] > df['9_EMA'], 1, 0)

        return df

    def calculate_rsi(self, df):
        n = 14  # period or number of look back days when calculating

        close = df['close']  # current days closing price
        close_past = df['close'].shift(1)  # previous days closing price
        close_delta = close - close_past  # change in closing price
        # positive or negative if above or below 0, this will determine if the price went up or down
        delta_sign = np.sign(close_delta)

        df['up_moves'] = np.where(
            delta_sign > 0, close_delta, 0)  # shows up trend
        df['down_moves'] = np.where(
            delta_sign < 0, close_delta.abs(), 0)  # shows down trend
        # calculate moving average up moves over 14 days
        avg_d = df['down_moves'].rolling(n).mean()
        # calculate moving average down moves over 14 days
        avg_u = df['up_moves'].rolling(n).mean()

        rs = avg_u / avg_d  # calculate relative strength
        rsi = 100 - 100 / (1 + rs)  # calculate relative strength index
        df['rsi'] = rsi
        df.dropna(inplace=True)

        # upper and lower bounds of the rsi trading signal
        upper_bound = 50
        lower_bound = 25

        # # calculate buy and sell signals depending on the upper and lower bounds
        df['upper_bound'] = np.where(df['rsi'] >= upper_bound, 1, 0)
        df['lower_bound'] = np.where(df['rsi'] <= lower_bound, 1, 0)

        return df

    # gets bar data for crypto ticker, timezone is UTC (universal time)
    def price_data(self, tickers):
        for ticker in tickers:
            now = dt.datetime.today()
            # now = now.strftime("%Y-%m-%d")
            request = CryptoBarsRequest(
                symbol_or_symbols=ticker, timeframe=TimeFrame.Minute, start=now)
            data = self.crypto_client.get_crypto_bars(request)
            print(data)
            data = data.df
            # print(data.head())
            try:
                data = data[data['exchange'] == 'CBSE']
            except Exception as e:
                print(e)
            data = Crypto_RSI_Crossover_Bot.calculate_cross_over(self, data)
            data = Crypto_RSI_Crossover_Bot.calculate_rsi(self, data)

            data['buy'] = np.where((data['upper_bound'] == 1) & (
                data['golden_cross'] == 1), 1, 0)
            # data['sell'] = np.where((data['lower_bound'] == 1) & (data['death_cross'] == 1), 1, 0)

            data.to_csv(
                './evans_quant/logs/crypto/rsi_crossover/{}.csv'.format(ticker.replace('/', '')))

    def execute_trade(self, df, ticker):

        api = self.api
        current = df.iloc[len(df.index) - 2]

        try:
            if current['buy'] == 1:  # using the most recent buy signal

                print('buy: {}'.format(ticker))
                request = MarketOrderRequest(
                    symbol=ticker,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.IOC,
                    # qty=1, # for buying a part of a BTC

                    # every order should be 5%-10% of your total portfolio
                    # for buying a fixed USD price amount of BTC
                    notional=round(float(self.account.buying_power) * .02),

                    # stop_loss={'stop_price' : current['close'] - (current['close'] * .3)} # price drops below 30 percent of current closing price = exit position

                    # stoploss at 10 percent current closing price
                    stop_loss={
                        'stop_price': current['close'] - (current['close'] * .1)},
                    # take profit at 20 percent over the current closing price
                    take_profit={
                        'limit_price': current['close'] + (current['close'] * .2)}
                )
                api.submit_order(request)

        except Exception as e:
            print('Failed to buy {}'.format(ticker))
            print(e)

    def main(self):
        tickers = ['BTC/USD', 'ETH/USD', 'LTC/USD', 'BCH/USD']
        # Get_Data.price_data(tickers)
        Crypto_RSI_Crossover_Bot.price_data(self, tickers)
        # Bot.trades_data(self, tickers)
        print(os.path)
        for ticker in tickers:
            # ticker = 'BTCUSD'
            df = pd.read_csv(
                './evans_quant/logs/crypto/rsi_crossover/{}.csv'.format(ticker.replace('/', '')))
            Crypto_RSI_Crossover_Bot.execute_trade(self, df, ticker)


if __name__ == '__main__':
    while True:

        bot = Crypto_RSI_Crossover_Bot()
        bot.main()
        time.sleep(60)
