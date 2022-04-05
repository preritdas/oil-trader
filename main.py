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
position = 0
alerted_me = False
market_clock_set = 8 # non weekday value

# Instantiate Alpaca API
alpaca = alpaca_api.REST(
    key_id = _keys.alpaca_API_key,
    secret_key = _keys.alpaca_API_secret,
    base_url = _keys.alpaca_endpoint
)

def account_performance(rounding: int):
    """
    Returns a rounded percentage value of the account's performance.
    If the account is up 1.23456%, and rounding = 3, it will return 1.234.
    """
    account = alpaca.get_account()
    change = float(account.equity) - float(account.last_equity)
    proportion = change/float(account.last_equity)
    percent = 100 * proportion
    return round(percent, rounding)

def store_performance():
    """
    Finds (creates if non-existent) a performance.csv file to write 
        account performance to every day.
    """
    performance = account_performance(rounding = 4)
    if not os.path.isfile('Data/performance.csv'):
        with open('Data/performance.csv', 'a') as f:
            # Create the file and write without a new line
            f.write(f'{kit.today_date()},{performance}')
    else:
        with open('Data/performance.csv', 'a') as f:
            # Write with a new line
            f.write(f'\n{kit.today_date()},{performance}')

def ideal_quantity(allocation: float = ideal_allocation, symbol: str = symbol):
    """
    Calculates the ideal position quantity based on allocation and symbol.
    All args are optional. By default, it uses global parameter's symbol
        and allocation.
    """
    account = alpaca.get_account()
    value = float(account.equity)
    ideal_size = value * allocation
    return math.ceil(ideal_size/current_price(symbol = symbol))

def current_price(symbol: str = symbol):
    """
    Returns a float of the current price of a symbol using the Alpaca API.
    Args are optional; by default, symbol is taken from global parameters.
    """
    response = alpaca.get_snapshot(symbol = symbol).latest_trade
    return float(response.p)

def get_data(symbol: str = symbol):
    """
    Gets a DataFrame of stock minute data from Alpaca's API.
    Takes symbol parameter which defaults to the symbol
        from the global parameter.
    """
    # Set the timeframe
    minute_timeframe = alpaca_api.TimeFrame(
        amount = 1, 
        unit = alpaca_api.TimeFrameUnit.Minute
    )
    
    # Get data
    barset = alpaca.get_bars(
        symbol = symbol,
        timeframe = minute_timeframe,
    )
    return barset.df

def current_ADX(data: pd.DataFrame = None):
    """
    Uses stockstats to calculate the current ADX when given a data DataFrame.
    data argument is optional; by default, uses the get_data function.
    """
    # Get the data here instead of in default parameters.
    if data is None: # if it wasn't given in parameters
        data = get_data()
    data = ss.StockDataFrame.retype(data)
    adx = data[["adx"]]
    current_row = adx.iloc[len(data) - 1]
    return float(current_row[0])

def moving_average(interval: int, data: pd.DataFrame = None):
    """
    Locally calculates a 'tailed average' (explained in the read-me) 
        when given data. By default, data DataFrame is taken using get_data.
    """
    # Get the data here instead of in default parameters.
    if data is None:
        data = get_data()
    working_data = data.tail(interval)
    closes = list(working_data['close'])
    average = sum(closes)/len(closes)
    return average

def bot_status():
    """
    Uses position variable to determine if the bot is long, short, or flat.
    """
    if position == 0:
        return "flat"
    elif position < 0:
        return f'short {position * -1}'
    elif position > 0:
        return f'long {position}'
    else:
        return 'position error in bot_status function.'

def trade_logic(data: pd.DataFrame = None):
    """
    Takes in a DataFrame (by default, comes from the get_data function)
        and makes buy and sell decisions. Uses multiprocessing to submit
        orders. All parameters are taken from global parameters or the
        outputs of other functions.
    """
    # Get the data here instead of in default parameters.
    if data is None:
        data = get_data()

    # Make position variable global for access in various iterations
    global position

    if(
        current_price() > moving_average(interval = timeframe, data = data) 
        and current_ADX(data = data) > 35 
        and position < 1
    ):
        # Buy
        print(f"Taking a trade. Long {symbol}.")
        texts.text_me(f"Oil trader went long on {symbol}.")
        # Multiprocessing
        def buy_order():
            alpaca.submit_order(
                symbol = symbol,
                qty = ideal_quantity(),
                side = 'buy'
            )
        mp.Process(target = buy_order).start()

        # Position management
        position += 1

    elif(
        current_price() < moving_average(interval = timeframe, data = data) 
        and current_ADX(data = data) > 35 
        and position > -1
    ):
        # Sell
        print(f"Taking a trade. Short {symbol}.")
        texts.text_me(f"Oil trader went short on {symbol}.")
        # Multiprocessing
        def sell_order():
            alpaca.submit_order(
                symbol = symbol,
                qty = ideal_quantity(),
                side = "sell"
            )
        mp.Process(target = sell_order).start()

        # Position management
        position -= 1

def main():
    """Main execution function. Takes no parameters."""

    # Make alerted_me and market_clock_set variables global
    global alerted_me
    global market_clock_set
    # Make position global for the close_all_positions() method
    global position

    # Deployment message
    print("Oil trader is alive and ready for action.")

    while True:
        time_decimal = kit.time_decimal()
        time_mins = kit.time_now(int_times = True)[1]
        if 6.75 <= time_decimal < 12.75 and time_mins % 15 == 0:
            # Alpaca clock with limited API calls (once per unique day)
            if market_clock_set != kit.weekday_int(): # it initially doesn't
                market_clock_set = kit.weekday_int()
                market_open = alpaca.get_clock().is_open
            # If market is closed, don't do the 'market is open' logic.
            if not market_open:
                continue

            # MAIN PROGRAM MARKET IS OPEN.
            print('Oil trader is running trade logic.')

            # inform me of being alive in the morning
            if alerted_me == False:
                texts.text_me("Oil trader is running trade logic.")
            alerted_me = True

            # Run trade logic
            trade_logic()
            print(
                "An iteration of trading logic has completed. Awaiting next iteration."
            )
            # Print bot status
            print(f"Oil Trader is currently {bot_status()}.")
            time.sleep(60) # time_mins % 60 will ensure this won't re-run
        elif 12.9 < time_decimal < 13 and market_open:
            # Close all positions
            alpaca.close_all_positions()
            print("All positions have been liquidated.")
            position = 0

            print("Done trading, sleeping for 5 mins before update.")
            time.sleep(0.1 * 3600) # so it doesn't run again
            print("Done trading for the day.")
            text_success = texts.text_me(
                f"Oil trader is done for the day. Today's performance: \
                    {account_performance(rounding = 4)}%."
            )
            # Message delivery success
            if text_success: 
                print("Update has been sent successfully.") 
            else:
                print("Unsuccessful delivery.")

            # Change alerted_me so it alerts next morning
            alerted_me = False

            # Update account performance with multiprocessing
            mp.Process(target = store_performance).start()

if __name__ == "__main__":
    main()