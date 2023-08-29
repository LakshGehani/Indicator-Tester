import matplotlib.pyplot as plt
from neo_api_client import NeoAPI
from datetime import datetime 
from matplotlib.ticker import MaxNLocator
from matplotlib.dates import date2num, DateFormatter

consumerkey = 'sZjdgrnQO7dYE4qj4nCjJ4vb4Uoa'
consumer_secret = 'MgzWAO3zRRafZgwCE5dDTl1t2roa'
Pan = 'DZGPG7699M'
Password = '@Lgsim4904'

ltp_values = []
plot_values = []
timestamps = []

def update_chart(timestamps, data):
    plt.clf()  
    plt.plot(timestamps,data)
    ax = plt.gca()
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))  # Show integers on the x-axis
    ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))  # Format the time as HH:MM:SS   
    plt.gcf().autofmt_xdate()
    plt.gca().yaxis.set_major_formatter(plt.FormatStrFormatter('%.2f'))
    plt.draw()
    plt.pause(0.01)

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
                
                # Clear the lists
                ltp_values.clear()

def on_message(message):
    try:
        ltp = float(message[0]['ltp'])
        print("Received LTP:", ltp)
        ltp_values.append(ltp)
        plot_values.append(ltp)

        now = datetime.now()
        timestamps.append(now) 
        update_chart(timestamps, plot_values)
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
        pass  #plot data
except KeyboardInterrupt:
    print("Stopping the script.")

