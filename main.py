from xml.etree.ElementTree import TreeBuilder
import alpaca_trade_api as alpaca_api
import stockstats as ss
import pandas as pd
from datetime import datetime as dt
import mypytoolkit as kit

import _keys

# ---- GLOBAL VARIABLES ----
symbol = 'USO'

# Instantiate Alpaca API
alpaca = alpaca_api.REST(
    key_id = _keys.alpaca_API_key,
    secret_key = _keys.alpaca_API_secret,
    base_url = _keys.alpaca_endpoint
)

def current_price(symbol: str = symbol):
    response = alpaca.get_snapshot(symbol = symbol).latest_trade
    return float(response.p)

def get_data():
    barset = alpaca.get_bars(
        symbol = symbol,
        timeframe = alpaca_api.TimeFrame.Minute,
    )
    return barset.df

def current_ADX(data: pd.DataFrame = get_data()):
    data = ss.StockDataFrame.retype(data)
    adx = data[["adx"]]
    current_row = adx.iloc[len(data) - 1]
    return float(current_row[0])

def moving_average(interval: int, data: pd.DataFrame = get_data()):
    working_data = data.tail(interval)
    closes = list(working_data['close'])
    average = sum(closes)/len(closes)
    return average

def trade_logic():
    data = get_data()
    if current_price() > moving_average(interval = 15, data = data) and current_ADX(data = data) > 35:
        # Buy
        alpaca.submit_order(
            symbol = symbol,
            qty = 1,
            side = 'buy'
        )
        in_long = True
    elif current_price() < moving_average(interval = 15, data = data) and current_ADX(data = data) > 35:
        # Sell
        alpaca.submit_order(
            symbol = symbol,
            qty = 1,
            side = "sell"
        )
        in_long = False

def main():
    while True:
        time_hours, time_mins = kit.time_now().split('-')
        time_hours, time_mins = int(time_hours), int(time_mins)
        if time_hours == 6 and time_mins >= 45:
            trade_logic()

if __name__ == "__main__":
    main()