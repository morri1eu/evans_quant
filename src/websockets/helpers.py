
def create_quotes_subscription_object(stock_tickers):
    """
    Create the subscription for the stock quotes.

    :param stock_tickers: The list of stock tickers to subscribe to.
    :return: The subscription.
    """
    # create comma separated string of stocks from stock_tickers list
    stocks_string = ','.join(stock_tickers)
    return {
        "action": "subscribe",
        "symbols": stocks_string,
    }


def get_eodhd_quote_websocket_url(api_key):
    """
    Get the websocket URL for the EOD Historical Data API.

    :param api_key: The API key for the EOD Historical Data API.
    :return: The websocket URL.
    """
    return f'wss://ws.eodhistoricaldata.com/ws/us-quote?api_token={api_key}'


def get_eodhd_crypto_websocket_url(api_key):
    """
    Get the websocket URL for the EOD Historical Data API.

    :param api_key: The API key for the EOD Historical Data API.
    :return: The websocket URL.
    """
    return f'wss://ws.eodhistoricaldata.com/ws/crypto?api_token={api_key}'


def create_crypto_subscription_object(crypto_tickers):
    """
    Create the subscription for the crypto quotes.

    :param crypto_tickers: The list of crypto tickers to subscribe to.
    :return: The subscription.
    """
    # create comma separated string of stocks from stock_tickers list
    crypto_string = ','.join(crypto_tickers)
    return {"action": "subscribe", "symbols": "ETH-USD"}
    # return {
    #     "action": "subscribe",
    #     "symbols": crypto_string,
    # }
