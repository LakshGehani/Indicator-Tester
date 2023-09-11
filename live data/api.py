import mysql.connector
import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf
from neo_api_client import NeoAPI
from datetime import datetime
import time 


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


def update_chart():

    df = fetch_data()

    if not df.empty:
         mpf.plot(df, type='candle', style='yahoo', title='Candlestick Chart',
                    ylabel='Price', show_nontrading=True)
         plt.show()
         time.sleep(60)


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
        save_to_database(current_time, first_value,
                         highest_value, lowest_value, last_value)
        fetch_data()
        update_chart()


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

        df.set_index('datetime', inplace=True)
    except Exception as e:
        print("Error:", e)

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    return df


def on_message(message):
    try:
        ltp = float(message[0]['ltp'])
        print("Received LTP:", ltp)
        ltp_values.append(ltp)
        plot_values.append(ltp)
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
