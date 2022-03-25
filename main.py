# Non-local imports
import alpaca_trade_api as alpaca_api
import stockstats as ss
import mypytoolkit as kit
import pandas as pd

# Local imports
import time
import math
import _keys
import texts
import multiprocessing as mp
import os

# ---- GLOBAL PARAMETERS ----
symbol = 'USO'
timeframe = 15 # minutes
ideal_allocation = 0.05 # position size

# Global variables
position = 'none'
alerted_me = False
market_clock_set = 8 # non weekday value

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

def store_performance():
    performance = account_performance(rounding = 4)
    if not os.path.isfile('Data/performance.csv'):
        with open('Data/performance.csv', 'a') as f:
            f.write(f'{kit.today_date()},{performance}')
    else:
        with open('Data/performance.csv', 'a') as f:
            f.write(f'\n{kit.today_date()},{performance}')

def ideal_quantity(allocation: float = ideal_allocation, symbol: str = symbol):
    account = alpaca.get_account()
    value = float(account.equity)
    ideal_size = value * allocation
    return math.ceil(ideal_size/current_price(symbol = symbol))

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
    # Make alerted_me variable global
    global alerted_me

    # Deployment message
    print("Oil trader is alive and ready for action.")

    while True:
        time_decimal = kit.time_decimal()
        time_mins = kit.time_now(int_times = True)[1]
        if 6.75 <= time_decimal < 12.75 and time_mins % 15 == 0:
            # DEBUG
            print('Oil trader is running trade logic.')

            # Alpaca clock with limited API calls (once per unique day)
            if market_clock_set != kit.weekday_int():
                market_clock_set = kit.weekday_int()
                if not alpaca.get_clock().is_open:
                    continue

            # inform me of being alive in the morning
            if alerted_me == False:
                texts.text_me("Oil trader is running trade logic.")
            alerted_me = True
            # Multiprocess the trade logic so as not to mess up timing
            mp.Process(target = trade_logic).start()
            print("An iteration of trading logic has completed. Awaiting next iteration.")
            time.sleep(60) # time_mins % 60 will ensure this won't re-run
        elif 12.9 < time_decimal < 13:
            print("Done trading, sleeping for 5 mins before update.")
            time.sleep(0.1 * 3600) # so it doesn't run again
            print("Done trading for the day.")
            text_response = texts.text_me(
                f"Oil trader is done for the day. Today's performance: {account_performance(rounding = 4)}%."
            )
            # Message delivery success
            print("Update has been sent successfully." if text_response else "Unsuccessful delivery.")

            # Change alerted_me so it alerts next morning
            alerted_me = False

            # Update account performance with multiprocessing
            mp.Process(target = store_performance).start()

if __name__ == "__main__":
    main()