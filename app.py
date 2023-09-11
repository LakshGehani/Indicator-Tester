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

default_atr_period = 3
default_multiplier = 2

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

    dcc.Graph(id='candlestick-chart'),

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


@app.callback(
    Output('candlestick-chart', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('atr-period-input', 'value'),
    Input('multiplier-input', 'value')
)
def update_candlestick_chart(n_intervals, atr_period, multiplier):

    df = fetch_data()
    supertrend_data = Supertrend(df, atr_period, multiplier)
    combined_df = pd.concat([df, supertrend_data], axis=1)

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

    return candlestick_chart


if __name__ == '__main__':
    app.run_server(debug=True)
