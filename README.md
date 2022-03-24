# Oil Trader

Oil Trader is a `$USO`-centered trading bot that currently corroborates average price movement with ADX. 

## Features

Oil Trader's features come in the form of locally defined functions. Some of them are independent while some call other local functions with default parameters. It's important to understand the behavior of each of these feature functions because they are frequently called within the program, and slight variations in their parameters can have severe differences in their behavior.

### Account Performance

`account_performance()` allows the bot to automatically calculate how well the underlying account (based on Alpaca API keys) has done in that day and append the data to a CSV file (Data/performance.csv) using `store_performance()`. If the file does not exist, it will create the file. Note that `store_performance()` calls `account_performance()` with a default parameter of `rounding = 4`. 

### Multiprocessing

Many aspects of Oil Trader don't necessarily have to be completed in the same process as the executor. For example, the process of submitting an order is slightly tedious as many account parameters have to be read, calculated, and altered, all while submitting values to Alpaca's REST API. 

So, certain processes (like order submission) are routed to another computing core to complete independently and simultaneously. This allows the `main.py` executor to continue running without being slowed down. 

Processes executed by other cores include:
- Order submission and execution
- Trade logic computation
- Calculating and storing account performance

### Ideal Quantity Calculation

Oil Trader will calculate the optimal position quantity based on the parameters given at the top of the program:

```python
# ---- GLOBAL PARAMETERS ----
symbol = 'USO'
timeframe = 15 # minutes
ideal_allocation = 0.05 # position size
```

This is not rigid. Every time the program runs through an iteration of `trade_logic()`, it recalculates the ideal position size (rounded up). So, if the account rises in value by enough to change the positional size, the program will reflect that change mid-day. The same is true vice versa, if the account loses value. This prevents losses from spiraling out of control while allowing the account's growth to potentially be exponential, not just linear.

### ADX Calculation

Oil Trader uses the `stockstats` library to aid in its calculation of current ADX. It gets live-historical data from Alpaca (calling historical data from the current minute as opposed to using a websocket). It outputs the latest ADX value (by minute). The `timeframe` from global parameters has no influence on this value.

### Tail Moving Average Calculation

The specified `timeframe` does matter in the moving average calculation, however. Oil Trader will input a DataFrame of minute-by-minute data and use the interval to calculate a tailed moving average based on the `timeframe`. This is a proprietary concept, leveraging multi-timeframe analysis with the elasticity of low-timeframe averages. 

### Logic and Update Timing

Oil Trader automatically wakes itself up and starts looking for trade opportunities at 6:45 a.m. PST (15 minutes after the market is open). With a default `timeframe` of 15 minutes, this allows enough data to accrue so Oil Trader is able to make decisions based solely on data from the same day (this is imperative). 

At 12:55 p.m. (5 minutes to market close) it will ensure it's no longer trading, sleep for six minutes, and then initiate its updates protocol in which it calculates the account performance, texts it to a user, and then appends the performance to the Data/performance.csv file as mentioned above. 

Because it sleeps for six minutes before executing the updates protocol, accidental re-running of the calculations, appendages, and text-messaging is out of the question. 

### Overall Independence

The program does not have to be re-run every day. It will automatically run updates when necessary and sleep until the market opens the next morning. It can be left running over weekends, too, because Oil Trader uses the `get_clock()` method from Alpaca to determine if the market is open before proceeding with the trade logic. 

## File Structure

Below is information on each file in the repository: what it does, how it works, and how to use it. An element missing from the section below is the `Data/` subdirectory which is necessary for `store_performance()` to work. Currently there is no protocol for creating the subdirectory itself if it doesn't exist, only the `performance.csv` file within the subdirectory. If you don't have a `Data/` subdirectory the program will crash at the end of the day with a `FileNotFoundError`. The subdirectory can (and probably should) be empty. Allow the program to populate it with data.

### main.py

The execution program. Run the program using `python main.py` and as long as all necessary dependencies are present (keys, modules, etc.) no errors will arise. 

### texts.py

The texting module. It uses the Nexmo SDK to create a few functions that are used in `main.py` to alert the user of various events. 

```python
## texts.py usage 

text_success = texts.text_me("Hello.") # returns a bool
print("Successful delivery" if text_success else "Failed.")

# Or...
if text_success:
    print("Successful delivery.")
else:
    print("Failed delivery.")
```

This works because the `texts.text_me()` function is written to return a boolean of whether the message went through. It calls Nexmo's API and checks for the first message send (usually there is only one unless a long message is divided into multiple deliveries). If the result is a `'0'` it returns `True`, otherwise it returns `False`. This simplicity allows for a simple success check as shown above.

### requirements.txt

All the Python requirements for this program to execute. Create a virtual environment, source the environment, and install all the dependencies using these commands. 

On Mac/Linux:
```shell
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Windows:
```shell
python -m venv venv
venv/Scripts/activate
pip install -r requirements.txt
```

### _keys.py

This is not included in the repository for obvious reasons but **is a required file for the program to work**. The `_keys.py` file **must** contain the following contents labeled in the same way such that `main.py` and `texts.py` can access the variables as written.

_keys.py
```python
# Alpaca
alpaca_endpoint = 'alpacaBaseUrl'
alpaca_API_key = 'alpacaAPIkey'
alpaca_API_secret = 'alpacaSecretKey'

# Nexmo
nexmo_api_key = 'nexmoAPIKey'
nexmo_api_secret = 'nexmoSecretKey'
nexmo_sender = 'nexmoRegisteredSenderNumber'
nexmo_my_number = 'userPhoneNumber'
```