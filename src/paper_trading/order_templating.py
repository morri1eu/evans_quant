import pandas as pd
import numpy as np


def get_orders_from_position_sizes(positions):
    orders = []
    for [stock_ticker, size] in positions:
        if size:
            orders.append([stock_ticker, size])

    orders_dataframe = pd.DataFrame(orders, columns=['Stock', 'Size'])
    return orders_dataframe
