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
import multiprocessing as mp

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

def account_performance(rounding: int):
    account = alpaca.get_account()
    change = float(account.equity) - float(account.last_equity)
    proportion = change/float(account.last_equity)
    percent = 100 * proportion
    return round(percent, rounding)

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

def trade_logic():
    # Make position variable global for access in various iterations
    global position

    data = get_data()
    if(
        current_price() > moving_average(interval = timeframe, data = data) 
        and current_ADX(data = data) > 35 
        and position != 'long'
    ):
        # Buy
        print(f"Taking a trade. Long {symbol}.")
        texts.text_me(f"Oil trader went long on {symbol}.")
        # Multiprocessing
        def buy_order():
            alpaca.submit_order(
                symbol = symbol,
                qty = ideal_quantity(allocation = 0.05, symbol = symbol),
                side = 'buy'
            )
        mp.Process(target = buy_order).start()

        position = 'long'
    elif(
        current_price() < moving_average(interval = timeframe, data = data) 
        and current_ADX(data = data) > 35 
        and position != 'long'
    ):
        # Sell
        print(f"Taking a trade. Short {symbol}.")
        texts.text_me(f"Oil trader went short on {symbol}.")
        # Multiprocessing
        def sell_order():
            alpaca.submit_order(
                symbol = symbol,
                qty = ideal_quantity(allocation = 0.05, symbol = symbol),
                side = "sell"
            )
        mp.Process(target = sell_order).start()
        
        position = 'short'

def main():
    print("Oil trader is alive and ready for action.")
    texts.text_me("Oil trader has just been deployed.")

    while True:
        time_decimal = kit.time_decimal()
        time_mins = kit.time_now(int_times = True)[1]
        if 6.75 <= time_decimal < 12.5 and time_mins % 15 == 0:
            # DEBUG
            print('Oil trader is running trade logic.')
            texts.text_me("Oil trader is running trade logic.")

            trade_logic()
            print("An iteration of trading logic has completed. Awaiting next iteration.")
            time.sleep(timeframe * 60)
        elif 12.9 < time_decimal < 13:
            print("Done trading, sleeping for 5 mins before update.")
            time.sleep(0.1 * 3600) # so it doesn't run again
            print("Done trading for the day.")
            texts.text_me(
                f"Oil trader is done for the day. Today's performance: {account_performance(rounding = 4)}%."
            )

if __name__ == "__main__":
    main()