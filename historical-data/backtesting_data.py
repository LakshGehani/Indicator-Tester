import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
import math
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

atr_period = 10
atr_multiplier = 3
investment = 10000000
lookback_period = 14
start ='2022-03-01'
symbol = '^NSEI'

df = yf.download(symbol, start)

def Supertrend(df, atr_period, multiplier):
    
    high = df['High']
    low = df['Low']
    close = df['Close']
    
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

def get_ci(high, low, close, lookback):
    tr1 = pd.DataFrame(high - low).rename(columns = {0:'tr1'})
    tr2 = pd.DataFrame(abs(high - close.shift(1))).rename(columns = {0:'tr2'})
    tr3 = pd.DataFrame(abs(low - close.shift(1))).rename(columns = {0:'tr3'})
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis = 1, join = 'inner').dropna().max(axis = 1)
    atr = tr.rolling(1).mean()
    highh = high.rolling(lookback).max()
    lowl = low.rolling(lookback).min()
    ci = 100 * np.log10((atr.rolling(lookback).sum()) / (highh - lowl)) / np.log10(lookback)
    return ci

def backtest_supertrend(df, investment):
    
    is_uptrend = df['Supertrend']
    df['ci_14'] = get_ci(df['High'], df['Low'], df['Close'], lookback_period)
    choppiness_index = df['ci_14']
    close = df['Close']
    
    # initial condition
    in_position = False
    equity = investment
    commission = 0
    share = 0
    entry = []
    exit = []
    
    for i in range(2, len(df)):
        # Check if Choppiness Index is below 61.80
        if choppiness_index[i] > 61.80:
            continue
        # if not in position & price is on uptrend -> buy
        if not in_position and is_uptrend[i]:
            share = math.floor(equity / close[i] / 100) * 100
            equity -= share * close[i]
            entry.append((i, close[i]))
            in_position = True
            print(f'Buy {share} shares at {round(close[i],2)} on {df.index[i].strftime("%Y/%m/%d")}')
        # if in position & price is not on uptrend -> sell
        elif in_position and not is_uptrend[i]:
            equity += share * close[i] - commission
            exit.append((i, close[i]))
            in_position = False
            print(f'Sell at {round(close[i],2)} on {df.index[i].strftime("%Y/%m/%d")}')
    # if still in position -> sell all share 
    if in_position:
        equity += share * close[i] - commission
    
    earning = equity - investment
    roi = round(earning/investment*100,2)
    print(f'Earning from investing ${investment} is ${round(earning,2)} (ROI = {roi}%)')
    return entry, exit, equity

def find_optimal_parameter(df):
    # predefine several parameter sets
    atr_period = [7, 8, 9, 10]
    atr_multiplier = [1.0, 1.5, 2.0, 2.5, 3.0]

    roi_list = []
    
    # for each period and multiplier, perform backtest
    for period, multiplier in [(x,y) for x in atr_period for y in atr_multiplier]:
        new_df = df
        supertrend = Supertrend(df, period, multiplier)
        new_df = df.join(supertrend)
        new_df = new_df[period:]
        entry, exit, roi = backtest_supertrend(new_df, 10000)
        roi_list.append((period, multiplier, roi))
    
    print(pd.DataFrame(roi_list, columns=['ATR_period','Multiplier','ROI']))
    
    # return the best parameter set
    return max(roi_list, key=lambda x:x[2])

optimal_param = find_optimal_parameter(df)
print(f'Best parameter set: ATR Period={optimal_param[0]}, Multiplier={optimal_param[1]}, ROI={optimal_param[2]}')   

atr_period = optimal_param[0]
atr_multiplier = optimal_param[1]


supertrend = Supertrend(df, atr_period, atr_multiplier)
df = df.join(supertrend)
df['ci_14'] = get_ci(df['High'], df['Low'], df['Close'], lookback_period)

highest_value = df[['High', 'Final Upperband']].max().max()
lowest_value = df[['Low', 'Final Lowerband']].min().min()
entry, exit, roi = backtest_supertrend(df, investment)


def plot_graph(df,entry_points,exit_points):

    fig = go.Figure()

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.3, row_heights=[0.8, 0.2])

    fig.add_trace(go.Candlestick(x=df.index,
                             open=df['Open'],
                             high=df['High'],
                             low=df['Low'],
                             close=df['Close'],
                             increasing_line_color= 'green', decreasing_line_color= 'red',
                             name='Stock Data'), row=1, col=1,
                             )
                             

    # Add 'Final Lowerband' to the first subplot (Candlestick chart)
    fig.add_trace(go.Scatter(x=df.index, y=df['Final Lowerband'], mode='lines', line=dict(color='green'), name='Final Lowerband'), row=1, col=1)
    fig.update_traces(line={'width': 1})

    # Add 'Final Upperband' to the first subplot (Candlestick chart)
    fig.add_trace(go.Scatter(x=df.index, y=df['Final Upperband'], mode='lines', line=dict(color='red'), name='Final Upperband'), row=1, col=1)
    fig.update_traces(line={'width': 1})
    
    for entry in entry_points:
        fig.add_trace(go.Scatter(x=[df.index[entry[0]]], y=[entry[1]], mode='markers', marker=dict(color='green', size=12, symbol='triangle-up'), name='Entry'), row=1, col=1)

    # Add Exit points
    for exit in exit_points:
        fig.add_trace(go.Scatter(x=[df.index[exit[0]]], y=[exit[1]], mode='markers', marker=dict(color='red', size=12, symbol='triangle-down'), name='Exit'), row=1, col=1)
    
    # Add Choppiness Index (CI) line to the second subplot
    fig.add_trace(go.Scatter(x=df.index,
                         y=df['ci_14'],
                         mode='lines',
                         name='Choppiness Index',
                         line=dict(color='red', width=2)), row=2, col=1)

    # Update the layout of the first subplot (Candlestick chart)
    fig.update_xaxes(title_text='Date', row=1, col=1)
    # Set Y-axis range for the first subplot (Candlestick chart)
    fig.update_yaxes(range=[lowest_value, highest_value],title_text='Price', row=1, col=1)
    fig.update_xaxes(
    mirror=True,
    ticks='outside',
    showline=True,
    linecolor='black',
    gridcolor='lightslategrey',
    row=1,col=1
)
    fig.update_yaxes(
    mirror=True,
    ticks='outside',
    showline=True,
    linecolor='black',
    gridcolor='lightslategrey',
    row=1,col=1
)

    # Update the layout of the second subplot (Choppiness Index plot)
    fig.update_xaxes(title_text='Date', row=2, col=1)
    fig.update_yaxes(title_text='Choppiness Index', row=2, col=1)

    fig.update_layout(plot_bgcolor='white')
    fig.update_layout(title_text=f'Stock Data for {symbol}', title_x=0.5)
    fig.show()

plot_graph(df,entry,exit)
