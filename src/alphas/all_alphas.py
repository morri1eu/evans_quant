# Importing the utility functions
from src.utils.functions_and_operators import *
from src.dataparsers.alpha_input_data_helpers import *

# Adjust Dataframes to have the same index here
# Alpha#1: Conditional Volatility Rank
def alpha1(df):
    returns = np.insert(extract_returns_from_df(df), 0, np.nan)
    close = extract_close_from_df(df)
    condition = returns < 0
    value = np.where(condition, stddev(returns, 20), close)
    return rank(ts_argmax(signedpower(value, 2), 5)) - 0.5

# Alpha#2: Volume and Price Change Correlation
# def alpha2(volume, close, open):
#     return -1 * correlation(rank(delta(log(volume), 2)), rank((close - open) / open), 6)


def alpha2(df):
    # Calculate the log volume and its delta
    log_volume = np.log(df['volume'])
    delta_log_volume = log_volume.diff(2)  # Change over 2 days

    # Calculate the normalized price change
    normalized_price_change = (df['close'] - df['open']) / df['open']

    # Rank the values
    rank_delta_log_volume = rank(delta_log_volume)
    rank_normalized_price_change = rank(normalized_price_change)

    # Calculate the correlation
    corr = rank_delta_log_volume.rolling(window=6).corr(rank_normalized_price_change)

    # Return the negative correlation as the signal
    return -1 * corr

def alpha3(df):
    # Rank the opening prices and volume
    rank_open = df['open'].rank()
    rank_volume = df['volume'].rank()

    # Calculate the rolling correlation
    rolling_corr = rank_open.rolling(window=10).corr(rank_volume)

    # Return the negative correlation as the signal
    return -1 * rolling_corr

# Alpha#4: Low Price Rank
# def alpha4(low):
#     return -1 * ts_rank(rank(low), 9)
def alpha4(df):
    # Calculate the rank of 'low' within the entire DataFrame
    df['low_rank'] = df['low'].rank(pct=True)

    # Calculate the rolling rank over the last 9 days of 'low_rank'
    # The rank is calculated with the 'min' method to handle ties by assigning them the minimum rank in the group
    df['ts_rank_low_rank'] = df['low_rank'].rolling(window=9, min_periods=1).apply(lambda x: x.rank(pct=True).iloc[-1])

    # Multiply by -1 as per the alpha formula
    df['alpha4'] = -1 * df['ts_rank_low_rank']

    return df['alpha4']

# Alpha#5: VWAP Deviation
def alpha5(df):
    # Calculate the 10-day rolling sum of 'vwap' and then divide by 10 to get the average
    df['vwap_10'] = df['vwap'].rolling(window=10, min_periods=1).sum() / 10

    # Calculate the rank of (open - vwap_10)
    df['rank_open_vwap_10'] = (df['open'] - df['vwap_10']).rank(pct=True)

    # Calculate the rank of (close - vwap) and then the absolute value of this rank
    df['abs_rank_close_vwap'] = abs((df['close'] - df['vwap']).rank(pct=True))

    # Calculate alpha5 by multiplying the two rank values and multiplying by -1
    df['alpha5'] = df['rank_open_vwap_10'] * (-1 * df['abs_rank_close_vwap'])

    return df['alpha5']


# Alpha#6: Open and Volume Correlation
# def alpha6(open_, volume):
#     return -1 * correlation(open_, volume, 10)
def alpha6(df):
    # Calculate the 10-day rolling correlation between 'open' and 'volume'
    df['alpha6'] = df['open'].rolling(window=10).corr(df['volume']) * -1
    return df['alpha6']

# Alpha#7: Conditional Delta Rank
# def alpha7(adv20, volume, close):
#     condition = adv20 < volume
#     delta_close = delta(close, 7)
#     value = -1 * ts_rank(abs(delta_close), 60) * sign(delta_close)
#     return np.where(condition, value, -1)
def alpha7(df):
    # Calculate the 20-day average daily volume
    df['adv20'] = df['volume'].rolling(window=20).mean()

    # Calculate the 7-day delta of 'close'
    df['delta_close_7'] = df['close'].diff(7)

    # Calculate the absolute rank of the 7-day delta of 'close' over a 60-day window
    df['rank_delta_close_7'] = df['delta_close_7'].abs().rolling(window=60).apply(lambda x: x.rank(pct=True).iloc[-1])

    # Calculate the sign of the 7-day delta of 'close'
    df['sign_delta_close_7'] = df['delta_close_7'].apply(np.sign)

    # Combine the rank and sign
    df['value'] = -1 * df['rank_delta_close_7'] * df['sign_delta_close_7']

    # Apply the condition
    df['alpha7'] = np.where(df['adv20'] < df['volume'], df['value'], -1)
    return df['alpha7']

# Alpha#8: Delayed Open-Returns Product Rank
def alpha8(df):
    # Calculate the 5-day sum of 'open'
    df['sum_open_5'] = df['open'].rolling(window=5).sum()

    # Calculate the 5-day sum of 'returns'
    df['sum_returns_5'] = df['returns'].rolling(window=5).sum()

    # Calculate the product of the sums
    df['product'] = df['sum_open_5'] * df['sum_returns_5']

    # Rank the difference between the product and its 10-day delay
    df['ranked_product'] = (df['product'] - df['product'].shift(10)).rank(pct=True)

    # Multiply by -1 as per the alpha definition
    df['alpha8'] = -1 * df['ranked_product']
    return df['alpha8']

# Alpha#9: Conditional Delta Close
def alpha9(df):
    # Calculate the 1-day delta of 'close'
    df['delta_close_1'] = df['close'].diff(1)

    # Calculate the 5-day min and max of the 1-day delta of 'close'
    df['ts_min_delta_close_5'] = df['delta_close_1'].rolling(window=5).min()
    df['ts_max_delta_close_5'] = df['delta_close_1'].rolling(window=5).max()

    # Apply the conditions
    condition1 = df['delta_close_1'] > df['ts_min_delta_close_5']
    condition2 = df['delta_close_1'] < df['ts_max_delta_close_5']
    df['alpha9'] = np.where(condition1, df['delta_close_1'], np.where(condition2, df['delta_close_1'], -1 * df['delta_close_1']))
    return df['alpha9']

# Alpha#10: Conditional Delta Close Rank
def alpha10(df):
    delta_close = df['close'].diff(1)
    condition1 = (delta_close > 0) & (delta_close.rolling(window=4).min() > 0)
    condition2 = (delta_close < 0) & (delta_close.rolling(window=4).max() < 0)
    value = np.where(condition1 | condition2, delta_close, -delta_close)
    df['alpha10'] = value.rank(pct=True)
    return df

# Alpha#11: VWAP-Close Delta Rank
def alpha11(df):
    vwap_close_delta = df['vwap'] - df['close']
    volume_delta = df['volume'].diff(3)
    df['alpha11'] = (vwap_close_delta.rolling(window=3).max().rank(pct=True) +
                     vwap_close_delta.rolling(window=3).min().rank(pct=True)) * volume_delta.rank(pct=True)
    return df

# Alpha#12: Sign of Volume Change Multiplied by Negative Close Change
def alpha12(df):
    df['alpha12'] = np.sign(df['volume'].diff()) * (-1 * df['close'].diff())
    return df

# Alpha#13: Negative Rank of Close-Volume Covariance
def alpha13(df):
    ranked_close = df['close'].rank(pct=True)
    ranked_volume = df['volume'].rank(pct=True)
    df['alpha13'] = -1 * ranked_close.rolling(window=5).cov(ranked_volume).rank(pct=True)
    return df

# Alpha#14: Returns and Open-Volume Correlation
def alpha14(returns, open_, volume):
    return -1 * rank(delta(returns, 3)) * correlation(open_, volume, 10)

# Alpha#15: High-Volume Correlation Sum Rank
def alpha15(high, volume):
    return -1 * sum_ts(rank(correlation(rank(high), rank(volume), 3)), 3)

# ... (and so on for other Alphas)
# ... (previous Alphas and utility functions)

# Alpha#16: High-Volume Covariance Rank
def alpha16(high, volume):
    return -1 * rank(covariance(rank(high), rank(volume), 5))

# Alpha#17: Complex Rank Expression
def alpha17(close, volume, adv20):
    return ((-1 * rank(ts_rank(close, 10))) * rank(delta(delta(close, 1), 1))) * rank(ts_rank((volume / adv20), 5))

# Alpha#18: Volatility and Correlation Rank
def alpha18(close, open_):
    return -1 * rank((stddev(abs(close - open_), 5) + (close - open_)) + correlation(close, open_, 10))

# Alpha#19: Long-Term Returns Rank
def alpha19(close, returns):
    return (-1 * sign((close - delay(close, 7)) + delta(close, 7))) * (1 + rank(1 + sum_ts(returns, 250)))

# Alpha#20: Open-Delayed High-Low-Close Rank
def alpha20(open_, high, low, close):
    return ((-1 * rank(open_ - delay(high, 1))) * rank(open_ - delay(close, 1))) * rank(open_ - delay(low, 1))

# Alpha#21: Conditional Close and Volume Rank
def alpha21(close, volume, adv20):
    condition1 = (sum_ts(close, 8) / 8) + stddev(close, 8)
    condition2 = sum_ts(close, 2) / 2
    condition3 = (volume / adv20)
    return np.where(condition1 < condition2, -1, np.where(condition2 < (condition1 - stddev(close, 8)), 1, np.where(condition3 >= 1, 1, -1)))

# Alpha#22: High-Volume Correlation Delta Rank
def alpha22(high, volume, close):
    return -1 * (delta(correlation(high, volume, 5), 5) * rank(stddev(close, 20)))

# Alpha#23: Conditional High Delta
def alpha23(high):
    condition = sum_ts(high, 20) / 20 < high
    return np.where(condition, -1 * delta(high, 2), 0)

# Alpha#24: Long-Term Close Delta
def alpha24(close):
    condition1 = delta((sum_ts(close, 100) / 100), 100) / delay(close, 100)
    condition2 = (condition1 < 0.05) | (condition1 == 0.05)
    return np.where(condition2, -1 * (close - ts_min(close, 100)), -1 * delta(close, 3))

# Alpha#25: Complex Rank Expression with VWAP
def alpha25(returns, adv20, vwap, high, close):
    return rank(((-1 * returns) * adv20 * vwap * (high - close)))

# ... (and so on for other Alphas)
def alpha_26(volume, high):
    return -1 * np.max(correlation(ts_rank(volume, 5), ts_rank(high, 5), 5), 3)

# Alpha#27: Conditional Alpha based on rank of sum of 6-day correlation of volume and vwap
def alpha_27(volume, vwap):
    rank_value = rank((np.sum(correlation(rank(volume), rank(vwap), 6), 2) / 2.0))
    return -1 if rank_value > 0.5 else 1

# Alpha#28: Scaled value of 5-day correlation of 20-day average volume and low, adjusted by close
def alpha_28(adv20, low, close, high):
    return scale(correlation(adv20, low, 5) + ((high + low) / 2) - close)

def alpha_29(close, returns, volume, adv20):
    part1 = np.min(product(rank(rank(scale(np.log(np.sum(ts_min(rank(rank(-1 * rank(delta(close - 1, 5)))), 2), 1))))), 1), 5)
    part2 = ts_rank(delay(-1 * returns, 6), 5)
    return part1 + part2

# Alpha#30: Involves ranking of sign of close price changes and volume
def alpha_30(close, volume):
    part1 = 1 - rank((sign(close - np.roll(close, 1)) + sign(np.roll(close, 1) - np.roll(close, 2)) + sign(np.roll(close, 2) - np.roll(close, 3))))
    part2 = np.sum(volume, 5) / np.sum(volume, 20)
    return part1 * part2

# Alpha#31: Involves multiple ranks and decay_linear function
def alpha_31(close, adv20, low):
    part1 = rank(rank(rank(decay_linear(-1 * rank(rank(delta(close, 10))), 10))))
    part2 = rank(-1 * delta(close, 3))
    part3 = sign(scale(correlation(adv20, low, 12)))
    return part1 + part2 + part3

# Your utility functions like ts_rank, correlation, etc. go here

# Alpha#32: Scaled sum of 7-day average close and 5-day delayed correlation between vwap and close
def alpha_32(close, vwap):
    return scale(np.sum(close, 7) / 7 - close) + 20 * scale(correlation(vwap, np.roll(close, 5), 230))

# Alpha#33: Rank of negative reciprocal of the ratio of open to close
def alpha_33(open_, close):
    return rank(-1 * ((1 - (open_ / close)) ** 1))

# Alpha#34: Rank of the difference between 2-day and 5-day standard deviation of returns and delta of close
def alpha_34(returns, close):
    return rank((1 - rank(np.std(returns, 2) / np.std(returns, 5))) + (1 - rank(delta(close, 1))))

# Alpha#35: Product of 32-day rank of volume and 16-day rank of price range, adjusted by 32-day rank of returns
def alpha_35(volume, close, high, low, returns):
    return (ts_rank(volume, 32) * (1 - ts_rank((close + high - low), 16))) * (1 - ts_rank(returns, 32))

# Alpha#36: Complex formula involving multiple ranks and correlations
def alpha_36(open_, close, volume, returns, high, adv20, vwap):
    part1 = 2.21 * rank(correlation((close - open_), np.roll(volume, 1), 15))
    part2 = 0.7 * rank(open_ - close)
    part3 = 0.73 * rank(ts_rank(np.roll(-1 * returns, 6), 5))
    part4 = rank(np.abs(correlation(vwap, adv20, 6)))
    part5 = 0.6 * rank(((np.sum(close, 200) / 200) - open_) * (close - open_))
    return part1 + part2 + part3 + part4 + part5

# Alpha#37: Sum of ranks of 1-day delayed correlation between open and close, and the difference between open and close
def alpha_37(open_, close):
    return rank(correlation(np.roll((open_ - close), 1), close, 200)) + rank(open_ - close)

# Alpha#38: Product of negative ranks of 10-day ts_rank of close and the ratio of close to open
def alpha_38(close, open_):
    return -1 * rank(ts_rank(close, 10)) * rank(close / open_)

# Alpha#39: Complex formula involving rank, delta, decay_linear, and sum
def alpha_39(close, volume, adv20, returns):
    part1 = -1 * rank(delta(close, 7) * (1 - rank(decay_linear(volume / adv20, 9))))
    part2 = 1 + rank(np.sum(returns, 250))
    return part1 * part2

# Alpha#40: Product of negative rank of 10-day standard deviation of high and 10-day correlation of high and volume
def alpha_40(high, volume):
    return -1 * rank(np.std(high, 10)) * correlation(high, volume, 10)

# Alpha#41: Square root of the product of high and low, adjusted by vwap
def alpha_41(high, low, vwap):
    return np.sqrt(high * low) - vwap

# Your utility functions like ts_rank, correlation, etc. go here

# Alpha#42: Rank of the difference between vwap and close divided by the sum of vwap and close
def alpha_42(vwap, close):
    return rank((vwap - close) / (vwap + close))

# Alpha#43: Product of 20-day ts_rank of volume to adv20 ratio and 8-day ts_rank of 7-day delta of close
def alpha_43(volume, adv20, close):
    return ts_rank(volume / adv20, 20) * ts_rank(-1 * delta(close, 7), 8)

# Alpha#44: Negative correlation between high and 5-day rank of volume
def alpha_44(high, volume):
    return -1 * correlation(high, rank(volume), 5)

# Alpha#45: Complex formula involving multiple ranks and correlations
def alpha_45(close, volume, vwap):
    part1 = rank(np.sum(np.roll(close, 5), 20) / 20)
    part2 = correlation(close, volume, 2)
    part3 = rank(correlation(np.sum(close, 5), np.sum(close, 20), 2))
    return -1 * (part1 * part2 * part3)

# Alpha#46: Conditional Alpha based on 10-day deltas of close
def alpha_46(close):
    condition = (((np.roll(close, 20) - np.roll(close, 10)) / 10) - ((np.roll(close, 10) - close) / 10))
    return -1 if condition < 0.25 else 1 if condition < 0 else -1 * (close - np.roll(close, 1))

# Alpha#47: Complex formula involving ranks, volume, and vwap
def alpha_47(close, volume, adv20, high, vwap):
    part1 = rank(1 / close) * volume / adv20
    part2 = high * rank(high - close) / (np.sum(high, 5) / 5)
    return part1 * part2 - rank(vwap - np.roll(vwap, 5))

# Alpha#48: Industry-neutralized complex formula
def alpha_48(close, IndClass):
    # IndClass.subindustry is a placeholder for the actual industry classification
    part1 = correlation(delta(close, 1), delta(np.roll(close, 1), 1), 250) * delta(close, 1) / close
    return indneutralize(part1, IndClass.subindustry) / np.sum((delta(close, 1) / np.roll(close, 1)) ** 2, 250)

# Alpha#49: Conditional Alpha based on 10-day deltas of close
def alpha_49(close):
    condition = ((np.roll(close, 20) - np.roll(close, 10)) / 10) - ((np.roll(close, 10) - close) / 10)
    return 1 if condition < -0.1 else -1 * (close - np.roll(close, 1))

# Alpha#50: Negative of the maximum rank of 5-day correlation of rank of volume and rank of vwap, over the last 5 days
def alpha_50(volume, vwap):
    return -1 * np.max(rank(correlation(rank(volume), rank(vwap), 5)), 5)


# Your utility functions like ts_rank, correlation, delta, etc. go here

# Alpha#51: Conditional Alpha based on 10-day deltas of close
def alpha_51(close):
    condition = ((np.roll(close, 20) - np.roll(close, 10)) / 10) - ((np.roll(close, 10) - close) / 10)
    return 1 if condition < -0.05 else -1 * (close - np.roll(close, 1))

# Alpha#52: Complex formula involving ts_min, returns, and volume
def alpha_52(low, returns, volume):
    part1 = -1 * ts_min(low, 5) + np.roll(ts_min(low, 5), 5)
    part2 = rank((np.sum(returns, 240) - np.sum(returns, 20)) / 220)
    return part1 * part2 * ts_rank(volume, 5)

# Alpha#53: Negative 9-day delta of a specific close-low-high formula
def alpha_53(close, low, high):
    return -1 * delta(((close - low) - (high - close)) / (close - low), 9)

# Alpha#54: Complex formula involving low, close, open, and high
def alpha_54(low, close, open_, high):
    return -1 * ((low - close) * (open_ ** 5)) / ((low - high) * (close ** 5))

# Alpha#55: Negative correlation between specific rank formulas involving close, low, high, and volume
def alpha_55(close, low, high, volume):
    part1 = rank((close - ts_min(low, 12)) / (ts_max(high, 12) - ts_min(low, 12)))
    return -1 * correlation(part1, rank(volume), 6)

# Alpha#56: Complex formula involving returns and market cap
def alpha_56(returns, cap):
    part1 = rank(np.sum(returns, 10) / np.sum(np.sum(returns, 2), 3))
    return 0 - (1 * part1 * rank(returns * cap))

# Alpha#57: Negative formula involving close, vwap, and ts_argmax
def alpha_57(close, vwap):
    return 0 - (1 * ((close - vwap) / decay_linear(rank(ts_argmax(close, 30)), 2)))

# Alpha#58: Industry-neutralized complex formula involving vwap and volume
def alpha_58(vwap, volume, IndClass):
    return -1 * ts_rank(decay_linear(correlation(indneutralize(vwap, IndClass.sector), volume, 3.92795), 7.89291), 5.50322)

# Alpha#59: Industry-neutralized complex formula involving vwap and volume
def alpha_59(vwap, volume, IndClass):
    adjusted_vwap = (vwap * 0.728317) + (vwap * (1 - 0.728317))
    return -1 * ts_rank(decay_linear(correlation(indneutralize(adjusted_vwap, IndClass.industry), volume, 4.25197), 16.2289), 8.19648)

# Alpha#60: Complex formula involving close, low, high, volume, and ts_argmax
def alpha_60(close, low, high, volume):
    part1 = 2 * scale(rank((((close - low) - (high - close)) / (high - low)) * volume))
    return 0 - (1 * (part1 - scale(rank(ts_argmax(close, 10)))))

# ... and that completes the Alphas

# Alpha#61: Rank comparison between VWAP and its minimum, and VWAP and ADV180 correlation
def alpha_61(vwap, adv180):
    return rank(vwap - ts_min(vwap, 16.1219)) < rank(correlation(vwap, adv180, 17.9282))

# Alpha#62: Complex rank comparison involving VWAP, ADV20, open, high, and low
def alpha_62(vwap, adv20, open_, high, low):
    return (rank(correlation(vwap, np.sum(adv20, 22.4101), 9.91009)) < rank(((rank(open_) + rank(open_)) < (rank((high + low) / 2) + rank(high)))) * -1)

# Alpha#63: Industry-neutralized complex formula involving close, VWAP, open, and ADV180
def alpha_63(close, vwap, open_, adv180, IndClass):
    part1 = rank(decay_linear(delta(indneutralize(close, IndClass.industry), 2.25164), 8.22237))
    adjusted_vwap = (vwap * 0.318108) + (open_ * (1 - 0.318108))
    part2 = rank(decay_linear(correlation(adjusted_vwap, np.sum(adv180, 37.2467), 13.557), 12.2883))
    return (part1 - part2) * -1

def alpha_64(open_, vwap, adv120, high, low):
    part1 = rank(correlation(np.sum((open_ * 0.178404) + (low * (1 - 0.178404)), 12.7054), np.sum(adv120, 12.7054), 16.6208))
    part2 = rank(delta((((high + low) / 2) * 0.178404) + (vwap * (1 - 0.178404)), 3.69741))
    return (part1 < part2) * -1

# Alpha#65: Rank comparison between correlation of open, VWAP, ADV60 and open minimum
def alpha_65(open_, vwap, adv60):
    part1 = rank(correlation((open_ * 0.00817205) + (vwap * (1 - 0.00817205)), np.sum(adv60, 8.6911), 6.40374))
    part2 = rank(open_ - ts_min(open_, 13.635))
    return (part1 < part2) * -1

# Alpha#66: Rank comparison involving VWAP, low, open, and high
def alpha_66(vwap, low, open_, high):
    part1 = rank(decay_linear(delta(vwap, 3.51013), 7.23052))
    part2 = ts_rank(decay_linear((((low * 0.96633) + (low * (1 - 0.96633))) - vwap) / (open_ - ((high + low) / 2)), 11.4157), 6.72611)
    return (part1 + part2) * -1

# Alpha#67: Rank comparison involving high, VWAP, ADV20, and sector/subindustry classification
def alpha_67(high, vwap, adv20, sector, subindustry):
    part1 = rank(high - ts_min(high, 2.14593))
    part2 = rank(correlation(indneutralize(vwap, sector), indneutralize(adv20, subindustry), 6.02936))
    return (part1 ** part2) * -1

# Alpha#68: Rank comparison involving high, ADV15, close, and low
def alpha_68(high, adv15, close, low):
    part1 = ts_rank(correlation(rank(high), rank(adv15), 8.91644), 13.9333)
    part2 = rank(delta(((close * 0.518371) + (low * (1 - 0.518371))), 1.06157))
    return (part1 < part2) * -1

# Alpha#69: Rank comparison involving VWAP, close, ADV20, and industry classification
def alpha_69(vwap, close, adv20, industry):
    part1 = rank(ts_max(delta(indneutralize(vwap, industry), 2.72412), 4.79344))
    part2 = ts_rank(correlation(((close * 0.490655) + (vwap * (1 - 0.490655))), adv20, 4.92416), 9.0615)
    return (part1 ** part2) * -1

# Alpha#70: Rank comparison involving VWAP, close, ADV50, and industry classification
def alpha_70(vwap, close, adv50, industry):
    part1 = rank(delta(vwap, 1.29456))
    part2 = ts_rank(correlation(indneutralize(close, industry), adv50, 17.8256), 17.9171)
    return (part1 ** part2) * -1

# Alpha#71: Max of two Ts_Rank involving close, adv180, low, open, and vwap
def alpha_71(close, adv180, low, open_, vwap):
    part1 = ts_rank(decay_linear(correlation(ts_rank(close, 3.43976), ts_rank(adv180, 12.0647), 18.0175), 4.20501), 15.6948)
    part2 = ts_rank(decay_linear((rank(((low + open_) - (vwap + vwap))) ** 2), 16.4662), 4.4388)
    return max(part1, part2)

# Alpha#72: Rank comparison involving high, low, adv40, vwap, and volume
def alpha_72(high, low, adv40, vwap, volume):
    part1 = rank(decay_linear(correlation(((high + low) / 2), adv40, 8.93345), 10.1519))
    part2 = rank(decay_linear(correlation(ts_rank(vwap, 3.72469), ts_rank(volume, 18.5188), 6.86671), 2.95011))
    return part1 / part2

# Alpha#73: Max of two ranks involving vwap, open, and low
def alpha_73(vwap, open_, low):
    part1 = rank(decay_linear(delta(vwap, 4.72775), 2.91864))
    part2 = ts_rank(decay_linear(((delta(((open_ * 0.147155) + (low * (1 - 0.147155))), 2.03608) / ((open_ * 0.147155) + (low * (1 - 0.147155)))) * -1), 3.33829), 16.7411)
    return max(part1, part2) * -1

# Alpha#74: Rank comparison involving close, adv30, high, vwap, and volume
def alpha_74(close, adv30, high, vwap, volume):
    part1 = rank(correlation(close, sum(adv30, 37.4843), 15.1365))
    part2 = rank(correlation(rank(((high * 0.0261661) + (vwap * (1 - 0.0261661)))), rank(volume), 11.4791))
    return (part1 < part2) * -1

# Alpha#75: Rank comparison involving vwap, volume, low, and adv50
def alpha_75(vwap, volume, low, adv50):
    part1 = rank(correlation(vwap, volume, 4.24304))
    part2 = rank(correlation(rank(low), rank(adv50), 12.4413))
    return part1 < part2

# Alpha#76: Max of two ranks involving vwap, low, adv81, and adv40
def alpha_76(vwap, low, adv81, adv40):
    part1 = rank(decay_linear(delta(vwap, 1.24383), 11.8259))
    part2 = ts_rank(decay_linear(ts_rank(correlation(indneutralize(low, 'sector'), adv81, 8.14941), 19.569), 17.1543, 19.383))
    return max(part1, part2) * -1

# Alpha#77: Min of two ranks involving high, low, vwap, and adv40
def alpha_77(high, low, vwap, adv40):
    part1 = rank(decay_linear(((((high + low) / 2) + high) - (vwap + high)), 20.0451))
    part2 = rank(decay_linear(correlation(((high + low) / 2), adv40, 3.1614), 5.64125))
    return min(part1, part2)

# Alpha#78: Rank comparison involving low, vwap, adv40, and volume
def alpha_78(low, vwap, adv40, volume):
    part1 = rank(correlation(sum(((low * 0.352233) + (vwap * (1 - 0.352233))), 19.7428), sum(adv40, 19.7428), 6.83313))
    part2 = rank(correlation(rank(vwap), rank(volume), 5.77492))
    return part1 ** part2

# Alpha#79: Rank comparison involving close, open, vwap, adv150
def alpha_79(close, open_, vwap, adv150):
    part1 = rank(delta(indneutralize(((close * 0.60733) + (open_ * (1 - 0.60733))), 'sector'), 1.23438))
    part2 = rank(correlation(ts_rank(vwap, 3.60973), ts_rank(adv150, 9.18637), 14.6644))
    return part1 < part2

# Alpha#80: Rank comparison involving open, high, adv10
def alpha_80(open_, high, adv10):
    part1 = rank(sign(delta(indneutralize(((open_ * 0.868128) + (high * (1 - 0.868128))), 'industry'), 4.04545)))
    part2 = ts_rank(correlation(high, adv10, 5.11456), 5.53756)
    return (part1 ** part2) * -1

# Alpha#81: Rank comparison involving vwap, adv10, and volume
def alpha_81(vwap, adv10, volume):
    part1 = rank(log(product(rank(rank(correlation(vwap, sum(adv10, 49.6054), 8.47743)**4)), 14.9655)))
    part2 = rank(correlation(rank(vwap), rank(volume), 5.07914))
    return (part1 < part2) * -1

# Alpha#82: Min of two ranks involving open, volume, and adv40
def alpha_82(open_, volume, adv40):
    part1 = rank(decay_linear(delta(open_, 1.46063), 14.8717))
    part2 = ts_rank(decay_linear(correlation(indneutralize(volume, 'sector'), ((open_ * 0.634196) + (open_ * (1 - 0.634196))), 17.4842), 6.92131), 13.4283)
    return min(part1, part2) * -1

# Alpha#83: Rank comparison involving high, low, close, volume, and vwap
def alpha_83(high, low, close, volume, vwap):
    part1 = rank(delay(((high - low) / (sum(close, 5) / 5)), 2))
    part2 = rank(rank(volume))
    part3 = ((high - low) / (sum(close, 5) / 5)) / (vwap - close)
    return (part1 * part2) / part3

# Alpha#84: Signed power of rank involving vwap and close
def alpha_84(vwap, close):
    return signedpower(ts_rank((vwap - ts_max(vwap, 15.3217)), 20.7127), delta(close, 4.96796))

# Alpha#85: Rank comparison involving high, close, adv30, low, and volume
def alpha_85(high, close, adv30, low, volume):
    part1 = rank(correlation(((high * 0.876703) + (close * (1 - 0.876703))), adv30, 9.61331))
    part2 = rank(correlation(ts_rank(((high + low) / 2), 3.70596), ts_rank(volume, 10.1595), 7.11408))
    return part1 ** part2

# Alpha#86: Rank comparison involving close, adv20, open, and vwap
def alpha_86(close, adv20, open_, vwap):
    part1 = ts_rank(correlation(close, sum(adv20, 14.7444), 6.00049), 20.4195)
    part2 = rank(((open_ + close) - (vwap + open_)))
    return (part1 < part2) * -1

# Alpha#87: Max of two ranks involving close, vwap, adv81, and industry classification
def alpha_87(close, vwap, adv81):
    part1 = rank(decay_linear(delta(((close * 0.369701) + (vwap * (1 - 0.369701))), 1.91233), 2.65461))
    part2 = ts_rank(decay_linear(abs(correlation(indneutralize(adv81, 'industry'), close, 13.4132)), 4.89768), 14.4535)
    return max(part1, part2) * -1

# Alpha#88: Min of two ranks involving open, low, high, close, adv60
def alpha_88(open_, low, high, close, adv60):
    part1 = rank(decay_linear(((rank(open_) + rank(low)) - (rank(high) + rank(close))), 8.06882))
    part2 = ts_rank(decay_linear(correlation(ts_rank(close, 8.44728), ts_rank(adv60, 20.6966), 8.01266), 6.65053), 2.61957)
    return min(part1, part2)

# Alpha#89: Difference of two Ts_Ranks involving low, adv10, vwap, and industry classification
def alpha_89(low, adv10, vwap):
    part1 = ts_rank(decay_linear(correlation(((low * 0.967285) + (low * (1 - 0.967285))), adv10, 6.94279), 5.51607), 3.79744)
    part2 = ts_rank(decay_linear(delta(indneutralize(vwap, 'industry'), 3.48158), 10.1466), 15.3012)
    return part1 - part2

# Alpha#90: Rank comparison involving close, low, adv40, adv10, and subindustry classification
def alpha_90(close, low, adv40, adv10):
    part1 = rank((close - ts_max(close, 4.66719)))
    part2 = ts_rank(correlation(indneutralize(adv40, 'subindustry'), low, 5.38375), 3.21856)
    return (part1 ** part2) * -1

# Alpha#91: Complex rank comparison involving close, volume, vwap, and industry classification
def alpha_91(close, volume, vwap, adv30):
    part1 = ts_rank(decay_linear(decay_linear(correlation(indneutralize(close, 'industry'), volume, 9.74928), 16.398), 3.83219), 4.8667)
    part2 = rank(decay_linear(correlation(vwap, adv30, 4.01303), 2.6809))
    return (part1 - part2) * -1

# Alpha#92: Min of two Ts_Ranks involving high, low, close, open, and adv30
def alpha_92(high, low, close, open_, adv30):
    part1 = ts_rank(decay_linear(((((high + low) / 2) + close) < (low + open_)), 14.7221), 18.8683)
    part2 = ts_rank(decay_linear(correlation(rank(low), rank(adv30), 7.58555), 6.94024), 6.80584)
    return min(part1, part2)

# Alpha#93: Ts_Rank divided by rank involving vwap, adv81, close, and industry classification
def alpha_93(vwap, adv81, close):
    part1 = ts_rank(decay_linear(correlation(indneutralize(vwap, 'industry'), adv81, 17.4193), 19.848), 7.54455)
    part2 = rank(decay_linear(delta(((close * 0.524434) + (vwap * (1 - 0.524434))), 2.77377), 16.2664))
    return part1 / part2

# Alpha#94: Rank power Ts_Rank involving vwap, adv60
def alpha_94(vwap, adv60):
    part1 = rank((vwap - ts_min(vwap, 11.5783)))
    part2 = ts_rank(correlation(ts_rank(vwap, 19.6462), ts_rank(adv60, 4.02992), 18.0926), 2.70756)
    return (part1 ** part2) * -1

# Alpha#95: Rank comparison involving open, high, low, adv40, adv30
def alpha_95(open_, high, low, adv40, adv30):
    part1 = rank((open_ - ts_min(open_, 12.4105)))
    part2 = ts_rank((rank(correlation(sum(((high + low) / 2), 19.1351), sum(adv40, 19.1351), 12.8742)) ** 5), 11.7584)
    return part1 < part2

# Alpha#96: Max of two Ts_Ranks involving vwap, volume, close, and adv60
def alpha_96(vwap, volume, close, adv60):
    part1 = ts_rank(decay_linear(correlation(rank(vwap), rank(volume), 3.83878), 4.16783), 8.38151)
    part2 = ts_rank(decay_linear(ts_argmax(correlation(ts_rank(close, 7.45404), ts_rank(adv60, 4.13242), 3.65459), 12.6556), 14.0365), 13.4143)
    return max(part1, part2) * -1

# Alpha#97: Rank difference involving low, vwap, adv60, and industry classification
def alpha_97(low, vwap, adv60):
    part1 = rank(decay_linear(delta(indneutralize(((low * 0.721001) + (vwap * (1 - 0.721001))), 'industry'), 3.3705), 20.4523))
    part2 = ts_rank(decay_linear(ts_rank(correlation(ts_rank(low, 7.87871), ts_rank(adv60, 17.255), 4.97547), 18.5925), 15.7152), 6.71659)
    return (part1 - part2) * -1

# Alpha#98: Rank difference involving vwap, adv5, open, and adv15
def alpha_98(vwap, adv5, open_, adv15):
    part1 = rank(decay_linear(correlation(vwap, sum(adv5, 26.4719), 4.58418), 7.18088))
    part2 = rank(decay_linear(ts_rank(ts_argmin(correlation(rank(open_), rank(adv15), 20.8187), 8.62571), 6.95668), 8.07206))
    return part1 - part2

# Alpha#99: Rank comparison involving high, low, adv60, volume
def alpha_99(high, low, adv60, volume):
    part1 = rank(correlation(sum(((high + low) / 2), 19.8975), sum(adv60, 19.8975), 8.8136))
    part2 = rank(correlation(low, volume, 6.28259))
    return (part1 < part2) * -1

# Alpha#100: Complex formula involving close, low, high, volume, adv20, and subindustry classification
def alpha_100(close, low, high, volume, adv20):
    part1 = 1.5 * scale(indneutralize(indneutralize(rank(((((close - low) - (high - close)) / (high - low)) * volume)), 'subindustry'), 'subindustry'))
    part2 = scale(indneutralize((correlation(close, rank(adv20), 5) - rank(ts_argmin(close, 30))), 'subindustry'))
    return 0 - (1 * (part1 - part2) * (volume / adv20))

# Alpha#101: Simple formula involving close, open, high, and low
def alpha_101(close, open_, high, low):
    return (close - open_) / ((high - low) + 0.001)