import pandas as pd


class BollingerBandsCalculator:
    def __init__(self, period=20, num_std_dev=2):
        self.period = period
        self.num_std_dev = num_std_dev
        self.price_data = pd.DataFrame()
        self.metrics = None
        self.current_support = None
        self.current_resistance = None
        self.current_moving_avg = None

    def add_price(self, price, symbol):
        # Add the new price to the DataFrame
        new_data = pd.DataFrame({'price': [price]}, index=[symbol])
        self.price_data = pd.concat([self.price_data, new_data])

        # Ensure we only keep the last 'period' prices
        if len(self.price_data) > self.period:
            self.price_data = self.price_data[-self.period:]

        # Calculate Bollinger Bands if we have enough data
        if len(self.price_data) == self.period:
            return self.calculate_bollinger_bands()
        else:
            return None

    def calculate_bollinger_bands(self):
        moving_avg = self.price_data['price'].rolling(
            window=self.period).mean()
        moving_std_dev = self.price_data['price'].rolling(
            window=self.period).std()

        upper_band = moving_avg + (moving_std_dev * self.num_std_dev)
        lower_band = moving_avg - (moving_std_dev * self.num_std_dev)
        self.current_support = lower_band.iloc[-1]
        self.current_resistance = upper_band.iloc[-1]
        self.current_moving_avg = moving_avg.iloc[-1]

        return lower_band.iloc[-1], upper_band.iloc[-1], moving_avg.iloc[-1]
