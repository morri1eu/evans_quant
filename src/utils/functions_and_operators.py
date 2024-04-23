import numpy as np
import pandas as pd

# Standard Functions

# Absolute Value: Converts all negative numbers in array x to positive.
def abs_val(x):
    return np.abs(x)

# Natural Logarithm: Computes the natural log of each element in array x.
def log(x):
    return np.log(x)

# Sign Function: Determines the sign of each element in array x.
# Positive numbers yield 1, negative numbers yield -1, and zero yields 0.
def sign(x):
    return np.sign(x)

# Cross-sectional Rank: Ranks each element in array x and returns an array of ranks.
# Useful for comparing elements to each other.
def rank(x):
    return pd.Series(x).rank(pct=True)

# Delay: Shifts array x by d days, filling the first d elements with NaN.
# Useful for comparing a series with its own past values.
def delay(x, d):
    return pd.Series(x).shift(d)

# Time-serial Correlation: Computes the correlation between arrays x and y over a rolling window of d days.
# Useful for identifying how two series move in relation to each other.
def correlation(x, y, d):
    return pd.Series(x).rolling(window=d).corr(pd.Series(y))

# Time-serial Covariance: Computes the covariance between arrays x and y over a rolling window of d days.
# Useful for identifying the directional relationship between two series.
def covariance(x, y, d):
    return pd.Series(x).rolling(window=d).cov(pd.Series(y))

# Scale: Scales array x so that the sum of its absolute values equals a.
# Useful for normalization.
def scale(x, a=1):
    return a * (x / np.sum(np.abs(x)))

# Delta: Computes the difference between each element in array x and its value d days ago.
# Useful for identifying changes over time.
def delta(x, d):
    return pd.Series(x).diff(d)

# Signed Power: Raises each element in array x to the power of a.
# Useful for amplifying the magnitude of elements.
def signedpower(x, a):
    return np.power(x, a)

# Decay Linear: Computes a weighted moving average on array x with a linearly decaying window of d days.
# Useful for smoothing data.
def decay_linear(x, d):
    weights = np.arange(1, d+1)
    weights = weights / np.sum(weights)
    return pd.Series(x).rolling(window=d).apply(lambda x: np.sum(weights * x))

# Industry Neutralize (Placeholder): Neutralizes array x against a given industry or sector grouping g.
# Useful for removing sector-specific influences from data.
def indneutralize(x, g):
    # Implement neutralization logic here
    return x

# Time-series Min: Finds the minimum value in array x over a rolling window of d days.
# Useful for identifying low points in data.
def ts_min(x, d):
    return pd.Series(x).rolling(window=d).min()

# Time-series Max: Finds the maximum value in array x over a rolling window of d days.
# Useful for identifying high points in data.
def ts_max(x, d):
    return pd.Series(x).rolling(window=d).max()

# Time-series Argmax: Finds the day on which the maximum value occurred in array x over a rolling window of d days.
# Useful for identifying when high points in data occurred.
def ts_argmax(x, d):
    return pd.Series(x).rolling(window=d).apply(np.argmax)

# Time-series Argmin: Finds the day on which the minimum value occurred in array x over a rolling window of d days.
# Useful for identifying when low points in data occurred.
def ts_argmin(x, d):
    return pd.Series(x).rolling(window=d).apply(np.argmin)

# Time-series Rank: Ranks each element in array x over a rolling window of d days.
# Useful for comparing elements to their past values.
def ts_rank(x, d):
    return pd.Series(x).rolling(window=d).apply(lambda x: rank(x)[-1])

# Time-series Sum: Computes the sum of elements in array x over a rolling window of d days.
# Useful for aggregating data over time.
def sum_ts(x, d):
    return pd.Series(x).rolling(window=d).sum()

# Time-series Product: Computes the product of elements in array x over a rolling window of d days.
# Useful for compound growth calculations.
def product(x, d):
    return pd.Series(x).rolling(window=d).apply(np.prod)

# Time-series Standard Deviation: Computes the standard deviation of elements in array x over a rolling window of d days.
# Useful for measuring volatility.
def stddev(x, d):
    return pd.Series(x).rolling(window=d).std()
