import matplotlib.pyplot as plt
from neo_api_client import NeoAPI
from datetime import datetime 
from matplotlib.ticker import MaxNLocator

consumerkey = 'sZjdgrnQO7dYE4qj4nCjJ4vb4Uoa'
consumer_secret = 'MgzWAO3zRRafZgwCE5dDTl1t2roa'
Pan = 'DZGPG7699M'
Password = '@Lgsim4904'

ltp_values = []
timestamps = []

def update_chart(data,timestamps):
    plt.clf()  
    plt.plot(timestamps,data)
    plt.gcf().autofmt_xdate() 
    plt.title('Real-time LTP Chart')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.gca().yaxis.set_major_formatter(plt.FormatStrFormatter('%.2f'))
    plt.draw()
    plt.pause(0.01)

def on_message(message):
    try:
        ltp = float(message[0]['ltp'])
        print("Received LTP:", ltp)
        ltp_values.append(ltp)
        #print("List of LTP values:", ltp_values)
        timestamps.append(datetime.now()) 
        update_chart(ltp_values, timestamps)
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

