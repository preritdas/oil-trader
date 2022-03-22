# Non-local imports
import alpaca_trade_api as alpaca_api
import stockstats as ss
import mypytoolkit as kit

# Local imports
import time
import math
import pandas as pd
from datetime import datetime as dt
import _keys
import texts

# ---- GLOBAL PARAMETERS ----
symbol = 'USO'
timeframe = 15 # minutes

# Global variables
position = 'none'

# Instantiate Alpaca API
alpaca = alpaca_api.REST(
    key_id = _keys.alpaca_API_key,
    secret_key = _keys.alpaca_API_secret,
    base_url = _keys.alpaca_endpoint
)

def account_performance():
    account = alpaca.get_account()
    change = float(account.equity) - float(account.last_equity)
    return change/float(account.last_equity)

def ideal_quantity(allocation: float = 0.05, symbol: str = symbol):
    account = alpaca.get_account()
    value = float(account.equity)
    ideal_size = value * allocation
    return math.ceil(ideal_size/current_price())

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

if(
    True == True and
    False == True
):
    print('hi')

def trade_logic():
    data = get_data()
    if(
        current_price() > moving_average(interval = timeframe, data = data) 
        and current_ADX(data = data) > 35 
        and position != 'long'
    ):
        # Buy
        print(f"Taking a trade. Long {symbol}.")
        alpaca.submit_order(
            symbol = symbol,
            qty = ideal_quantity(allocation = 0.05, symbol = symbol),
            side = 'buy'
        )
        position = 'long'
    elif(
        current_price() < moving_average(interval = timeframe, data = data) 
        and current_ADX(data = data) > 35 
        and position != 'long'
    ):
        # Sell
        print(f"Taking a trade. Short {symbol}.")
        alpaca.submit_order(
            symbol = symbol,
            qty = ideal_quantity(allocation = 0.05, symbol = symbol),
            side = "sell"
        )
        position = 'short'

def main():
    print("Oil trader is alive and ready.")
    texts.text_me("Oil trader has just been deployed.")

    while True:
        time_hours, time_mins = kit.time_now().split('-')
        time_hours, time_mins = int(time_hours), int(time_mins)
        if 6 <= time_hours < 12 and time_mins >= 45:
            trade_logic()
            print("An iteration of trading logic has completed. Awaiting next iteration.")
            time.sleep(timeframe * 60)
        elif time_hours == 12 and 55 < time_mins < 59:
            time.sleep(300)
            print("Done trading for the day.")
            texts.text_me(
                f"""
                Oil trader is done for the day. 
                Today's performance: {account_performance()}. 
                """
            )

if __name__ == "__main__":
    pass