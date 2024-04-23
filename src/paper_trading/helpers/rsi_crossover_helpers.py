from collections import deque
import numpy as np


class RSI_Calculator:
    def __init__(self, period=14):
        self.period = period
        self.price_buffer = deque(maxlen=period)
        self.gain_buffer = deque(maxlen=period)
        self.loss_buffer = deque(maxlen=period)
        self.current_rsi = None

    def add_price(self, price):
        if self.price_buffer:
            change = price - self.price_buffer[-1]
            gain = max(change, 0)
            loss = abs(min(change, 0))
            self.gain_buffer.append(gain)
            self.loss_buffer.append(loss)
        self.price_buffer.append(price)
        if len(self.price_buffer) == self.period:
            self.current_rsi = self.calculate_rsi()
            return self.current_rsi
        return None

    def on_updated_price(self, price):
        if self.price_buffer:
            change = price - self.price_buffer[-1]
            gain = max(change, 0)
            loss = abs(min(change, 0))
            self.gain_buffer[-1] = gain
            self.loss_buffer[-1] = loss
        self.price_buffer[-1] = price
        if len(self.price_buffer) == self.period:
            self.current_rsi = self.calculate_rsi()
            return self.current_rsi
        return None

    def calculate_rsi(self):
        avg_gain = np.mean(self.gain_buffer)
        avg_loss = np.mean(self.loss_buffer)
        print(f"Average Gain: {avg_gain}, Average Loss: {avg_loss}")
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        print(f"Calculated RSI: {rsi}")
        return rsi

    def get_rsi(self):
        return self.current_rsi

# Example usage
# rsi_calculator = RSI_Calculator(period=14)

# # Simulate receiving new price data from WebSocket
# for new_price in websocket_price_stream:
#     rsi = rsi_calculator.add_price(new_price)
#     if rsi is not None:
#         print(f"Updated RSI: {rsi}")
