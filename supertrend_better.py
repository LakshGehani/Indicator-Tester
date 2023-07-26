# -*- coding: utf-8 -*-
"""
Created on Mon Jul 24 17:23:10 2023

@author: laksh
"""

import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
import math
import matplotlib.pyplot as plt
import mplfinance as mpf

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
    
    # HL2 is simply the average of high and low prices
    hl2 = (high + low) / 2
    # upperband and lowerband calculation
    # notice that final bands are set to be equal to the respective bands
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
    
    
atr_period = 10
atr_multiplier = 3

symbol = 'BAJFINANCE.NS'
df = yf.download(symbol, start='2022-03-01')
supertrend = Supertrend(df, atr_period, atr_multiplier)
df = df.join(supertrend)
print(df)

plt.plot(df['Close'], label='Close Price')
plt.plot(df['Final Lowerband'], 'g', label = 'Final Lowerband')
plt.plot(df['Final Upperband'], 'r', label = 'Final Upperband')
plt.show()
#%%
def backtest_supertrend(df, investment):
    
    is_uptrend = df['Supertrend']
    close = df['Close']
    
    # initial condition
    in_position = False
    equity = investment
    commission = 5
    share = 0
    entry = []
    exit = []
    
    for i in range(2, len(df)):
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
    print(f'Earning from investing $10k is ${round(earning,2)} (ROI = {roi}%)')
    return entry, exit, equity
entry, exit, roi = backtest_supertrend(df, 10000)
#%%
# visualization (for backtest)

plt.figure(figsize=(16,9),dpi=360)
plt.plot(df['Close'], label='Close Price',linewidth=3)
plt.plot(df['Final Lowerband'],'g', label = 'Final Lowerband',linewidth=2)
plt.plot(df['Final Upperband'], 'r', label = 'Final Upperband',linewidth=2)
plt.legend()
for e in entry:
    plt.plot(df.index[e[0]], e[1], marker = '^', color = 'green', markersize = 12, linewidth = 0, label = 'Entry')
for e in exit:
    plt.plot(df.index[e[0]], e[1], marker = 'v', color = 'red', markersize = 12, linewidth = 0, label = 'Exit')
plt.show()

#%%
# Convert the DataFrame to a form suitable for mplfinance
df_mpf = df.copy()
df_mpf.index.name = 'Date'
df_mpf.reset_index(inplace=True)
df_mpf['Date'] = pd.to_datetime(df_mpf['Date'])
df_mpf.set_index('Date', inplace=True)  # Set 'Date' as the index

# Plot the data as a candlestick chart
mpf.plot(df_mpf, type='candle', style='yahoo', volume=False)
#%%
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

df = yf.download('TATASTEEL.NS', start='2020-01-01')
optimal_param = find_optimal_parameter(df)

print(f'Best parameter set: ATR Period={optimal_param[0]}, Multiplier={optimal_param[1]}, ROI={optimal_param[2]}')      
