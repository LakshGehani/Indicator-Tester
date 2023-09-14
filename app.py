import mysql.connector
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import numpy as np
import math

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '@Lgsimone4904',
    'database': 'tutorial'
}

default_atr_period = 14
default_multiplier = 2
starting_investment_amount = 100000000

external_stylesheets = ['styles.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Interactive Charts'

app.layout = html.Div([
    html.Div([
        html.Label('Multiplier', className="multiplier"),
        dcc.Input(id='multiplier-input', type='number',
                  value=default_multiplier, style={'display': 'inline-block'}),
    ]),

    html.Div([
        html.Label('ATR Period', className="atr-period"),
        dcc.Input(id='atr-period-input', type='number',
                  value=default_atr_period, style={'display': 'inline-block'}),
    ]),

    html.Div([
        html.Label('Starting Investment Amount', className="investment-amount"),
        dcc.Input(id='investment-input', type='number',
                  value=10000000, style={'display': 'inline-block'})
    ]),

    html.Div(dcc.Graph(id='candlestick-chart')),
    html.Div(id='backtest-results'),

    dcc.Interval(
        id='interval-component',
        interval=60 * 1000,
        n_intervals=0
    )
])

def fetch_data():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute("SELECT datetime, open, high, low, close FROM Data")
    data = cursor.fetchall()
    df = pd.DataFrame(
        data, columns=['datetime', 'open', 'high', 'low', 'close'])
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
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
    atr = true_range.ewm(alpha=1/atr_period, min_periods=atr_period).mean()
    # df['atr'] = df['tr'].rolling(atr_period).mean()

    # HL2 is the average of high and low prices
    hl2 = (high + low) / 2
    # upperband and lowerband calculation
    # final bands are set to be equal to the respective bands
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

def backtest_supertrend(df, investment):
    is_uptrend = df['Supertrend']
    close = df['close']
    
    # initial condition
    in_position = False
    equity = investment
    commission = 5
    share = 0
    entry = []
    exit = []
    buy_transactions = [] 
    sell_transactions = [] 
    
    for i in range(2, len(df)):
        # if not in position & price is on uptrend -> buy
        if not in_position and is_uptrend[i]:
            share = math.floor(equity / close[i] / 100) * 100
            equity -= share * close[i]
            entry.append((i, close[i]))
            buy_transactions.append((share, close[i], df.index[i]))  # Append to buy_transactions
            in_position = True
            print(f'Buy {share} shares at {round(close[i],2)} on {df.index[i].strftime("%H:%M:%S")}')
        # if in position & price is not on uptrend -> sell
        elif in_position and not is_uptrend[i]:
            equity += share * close[i] - commission
            exit.append((i, close[i]))
            sell_transactions.append((share, close[i], df.index[i]))  # Append to sell_transactions
            in_position = False
            print(f'Sell at {round(close[i],2)} at {df.index[i].strftime("%H:%M:%S")}')

    # if still in position -> sell all share 
    if in_position:
        equity += share * close[i] - commission
    
    earning = equity - investment
    roi = round(earning/investment*100,2)
    print(f'Earning from investing {starting_investment_amount} is ${round(earning,2)} (ROI = {roi}%)')
    
    return entry, exit, roi, buy_transactions, sell_transactions 
 

@app.callback(
    Output('candlestick-chart', 'figure'),
    Output('backtest-results', 'children'),
    Input('interval-component', 'n_intervals'),
    Input('atr-period-input', 'value'),
    Input('multiplier-input', 'value'),
    Input('investment-input', 'value')
)
def update_candlestick_chart(n_intervals, atr_period, multiplier, investment):
    global starting_investment_amount
    starting_investment_amount = investment
    df = fetch_data()
    supertrend_data = Supertrend(df, atr_period, multiplier)
    combined_df = pd.concat([df, supertrend_data], axis=1)
    entry, exit, roi, buy_transactions, sell_transactions = backtest_supertrend(combined_df, starting_investment_amount)
    candlestick_chart = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Candlesticks',
        showlegend=False,
    )])

    candlestick_chart.add_trace(go.Scatter(
        x=df.index,
        y=supertrend_data['Final Upperband'],
        mode='lines',
        name='Final Upperband',
        line=dict(color='red')
    ))
    candlestick_chart.add_trace(go.Scatter(
        x=df.index,
        y=supertrend_data['Final Lowerband'],
        mode='lines',
        name='Final Lowerband',
        line=dict(color='green')
    ))
    buy_signal_trace = go.Scatter(
        x=[buy[2] for buy in buy_transactions],
        y=[buy[1] for buy in buy_transactions],
        mode='markers',
        marker=dict(symbol='triangle-up', size=8, color='green'),
        name='Buy Signals'
    )

    sell_signal_trace = go.Scatter(
        x=[sell[2] for sell in sell_transactions], 
        y=[sell[1] for sell in sell_transactions], 
        mode='markers',
        marker=dict(symbol='triangle-down', size=8, color='red'),
        name='Sell Signals'
    )

    candlestick_chart.add_trace(buy_signal_trace)
    candlestick_chart.add_trace(sell_signal_trace)

    candlestick_chart.update_layout(
        title='BankNifty Data',
        xaxis_title='Time',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False,
        width=1250,
        height=600,
        yaxis=dict(
            tickformat='f'
        ),
        font=dict(
            family="verdana",
            size=12,
            color="white"
        ),
        plot_bgcolor="#f2f2f2",
        paper_bgcolor="black",
        margin=dict(
            l=50,
            r=50,
            b=100,
            t=100,
            pad=4
        ),
        hovermode="closest",
        legend=dict(
            font=dict(size=10),
            bgcolor="black",
            bordercolor="gray",
            borderwidth=1
        ),
        title_x=0.5,
        title_xanchor='center'
    )


    backtest_results_str = ''
    
    max_len = max(len(buy_transactions), len(sell_transactions))
    
    for i in range(max_len):
        if i < len(buy_transactions):
            buy = buy_transactions[i]
            backtest_results_str += f'Buy {buy[0]} shares at {buy[1]} on {buy[2].strftime("%H:%M:%S")}||'
        if i < len(sell_transactions):
            sell = sell_transactions[i]
            backtest_results_str += f'Sell at {sell[1]} at {sell[2].strftime("%H:%M:%S")}||'

    return candlestick_chart, backtest_results_str

if __name__ == '__main__':
    app.run_server()