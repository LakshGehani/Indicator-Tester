import mysql.connector
import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf
from neo_api_client import NeoAPI
from datetime import datetime
import time 
import numpy as np
import plotly.graph_objs as go 
from plotly.subplots import make_subplots


db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '@Lgsimone4904',
    'database': 'tutorial'
}

consumerkey = 'sZjdgrnQO7dYE4qj4nCjJ4vb4Uoa'
consumer_secret = 'MgzWAO3zRRafZgwCE5dDTl1t2roa'
Pan = 'DZGPG7699M'
Password = '@Lgsim4904'

ltp_values = []
plot_values = []
timestamps = []

atr_period = 3
multiplier = 2

def plot_graph():

    df = fetch_data()
    supertrend = Supertrend(df,atr_period,multiplier)
    fig = go.Figure()

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.3, row_heights=[0.8, 0.2])

    fig.add_trace(go.Candlestick(x=df.index,open=df['open'],high=df['high'],low=df['low'],close=df['close'],
                increasing_line_color= 'green', decreasing_line_color= 'red',name='Stock Data'), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=supertrend['Final Lowerband'], mode='lines', line=dict(color='green'), name='Final Lowerband'), row=1, col=1)
    fig.update_traces(line={'width': 1})

    fig.add_trace(go.Scatter(x=df.index, y=supertrend['Final Upperband'], mode='lines', line=dict(color='red'), name='Final Upperband'), row=1, col=1)
    fig.update_traces(line={'width': 1})
    fig.show()

def candle(ltp_values):
    if len(ltp_values) >= 60:
        first_value = ltp_values[0]
        last_value = ltp_values[-1]
        highest_value = max(ltp_values)
        lowest_value = min(ltp_values)

        print("First Value:", first_value)
        print("Last Value:", last_value)
        print("Highest Value:", highest_value)
        print("Lowest Value:", lowest_value)

        ltp_values.clear()
        current_time = datetime.now()
        save_to_database(current_time, first_value,highest_value, lowest_value, last_value)
        fetch_data()


def save_to_database(time, open, high, low, close):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        insert_query = "INSERT INTO Data (datetime, open, high, low, close) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (time, open, high, low, close))
        connection.commit()
        print(
            f"Candlestick data saved to the database: Time={time}, Open={open}, High={high}, Low={low}, Close={close}")
    except Exception as e:
        print("Error saving candlestick data to the database:", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def fetch_data():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        cursor.execute("SELECT datetime, open, high, low, close FROM Data")
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=['datetime', 'open', 'high', 'low', 'close'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        Supertrend(df,atr_period,multiplier)

        df.set_index('datetime', inplace=True)
    except Exception as e:
        print("Error:", e)

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    return df

def Supertrend(df, atr_period, multiplier):
    
    high = df['high']
    low = df['low']
    close = df['close']
    
    # calculate ATR
    price_diffs = [high - low, 
                   high - close.shift(), 
                   close.shift() - low]
    true_range = pd.concat(price_diffs, axis=1)
    true_range = true_range.abs().max(axis=1)
    # default ATR calculation in supertrend indicator
    atr = true_range.ewm(alpha=1/atr_period,min_periods=atr_period).mean() 
    # df['atr'] = df['tr'].rolling(atr_period).mean()
    
    # HL2 is the average of high and low prices
    hl2 = (high + low) / 2
    # upperband and lowerband calculation
    #final bands are set to be equal to the respective bands
    final_upperband = upperband = hl2 + (multiplier * atr)
    final_lowerband = lowerband = hl2 - (multiplier * atr)
    
    # initialize Supertrend column to True
    supertrend = [True] * len(df)
    
    for i in range(1, len(df.index)):
        curr, prev = i, i-1
        
        # if current close price crosses above upperband
        if close[curr] > final_upperband[prev]:
            supertrend[curr] = True
        # if current close price crosses below lowerband
        elif close[curr] < final_lowerband[prev]:
            supertrend[curr] = False
        # else, the trend continues
        else:
            supertrend[curr] = supertrend[prev]
            
            # adjustment to the final bands
            if supertrend[curr] == True and final_lowerband[curr] < final_lowerband[prev]:
                final_lowerband[curr] = final_lowerband[prev]
            if supertrend[curr] == False and final_upperband[curr] > final_upperband[prev]:
                final_upperband[curr] = final_upperband[prev]

        # to remove bands according to the trend direction
        if supertrend[curr] == True:
            final_upperband[curr] = np.nan
        else:
            final_lowerband[curr] = np.nan
    
    return pd.DataFrame({
        'Supertrend': supertrend,
        'Final Lowerband': final_lowerband,
        'Final Upperband': final_upperband
    }, index=df.index)

def on_message(message):
    try:
        ltp = float(message[0]['ltp'])
        print("Received LTP:", ltp)
        ltp_values.append(ltp)
        candle(ltp_values)
    except Exception as e:
        print("Error processing message:", e)

client = NeoAPI(consumer_key=consumerkey, consumer_secret=consumer_secret, environment='prod',
                on_message=on_message, on_error=None, on_close=None, on_open=None)

client.login(pan=Pan, password=Password)
otp = input("Enter OTP: ")
client.session_2fa(OTP=otp)

inst_tokens = [{"instrument_token": "26009", "exchange_segment": "nse_cm"}]
data_list = client.subscribe(instrument_tokens=inst_tokens)

try:
    while True:
        pass
except KeyboardInterrupt:
    print("Stopping the script.")
