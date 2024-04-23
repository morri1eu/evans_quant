class VWAPCalculator:
    def __init__(self):
        self.cumulative_total_price_volume = 0
        self.cumulative_volume = 0
        self.vwap = None

    def add_tick(self, price, volume):
        """
        Add a new tick (price and volume) to the VWAP calculation.
        :param price: The price of the tick.
        :param volume: The volume of the tick.
        """
        total_price_volume = price * volume
        self.cumulative_total_price_volume += total_price_volume
        self.cumulative_volume += volume

        if self.cumulative_volume != 0:
            self.vwap = self.cumulative_total_price_volume / self.cumulative_volume

    def get_vwap(self):
        """
        Get the current VWAP.
        :return: The current VWAP or None if no data has been added.
        """
        return self.vwap
