import alpaca_trade_api as tradeapi
import requests
import time
import talib
from datetime import datetime, timedelta
from pytz import timezone
import pytz    # $ pip install pytz
import tzlocal # $ pip install tzlocal
import matplotlib.pyplot as plt #python -mpip install -U matplotlib
from pandas.plotting import register_matplotlib_converters
import pandas as pd




# Replace these with your API connection info from the dashboard
base_url = 'https://paper-api.alpaca.markets'
api_key_id = 'PK3IJIUVKV5LS5NTD5GW'
api_secret = 'oypm2et3zPvEA35er7NHagdihl/QxgEfpBEFsOVX'

api = tradeapi.REST(
    base_url=base_url,
    key_id=api_key_id,
    secret_key=api_secret,
    api_version='v2'
)

session = requests.session()

local_timezone = pytz.timezone('US/Eastern') # get pytz tzinfo

def get_history_data(symbol,startTS,endTS,resampleRate):
    print('Getting historical data...')
    minute_history = {}
    minute_history[symbol] = api.polygon.historic_agg(
            size="minute", symbol=symbol, _from=startTS, to=endTS     ).df
    history=minute_history[symbol]['close'].resample(resampleRate).first().fillna(method='ffill')
    return history #minute_history[symbol]['close'].fillna(method='ffill').resample(resampleRate)


def macdStudy(history,fast,slow,signal):
    print('calculating macd data...')
    #MACD study
    macd, macdsignal, macdhist = talib.MACD(
        history,
        fastperiod=fast,
        slowperiod=slow,
        signalperiod=signal
    )
    return macd, macdsignal, (macd- macdsignal)

def backTest(history, qty, signalData, startTS, endTS):
    print('back testing between',startTS, 'and',endTS)
    buyTime=[]
    buyPrice=[]
    sellTime=[]
    sellPrice=[]
    profitLoss=0
    lastPrice=0
    bought=False
    i=0
    for y in history:
        if (history.index[i].astimezone(local_timezone)>=startTS and history.index[i].astimezone(local_timezone)<=endTS):
            lastPrice=y
            if (not bought and signalData[history.index[i]]>0):
                buyTime.append(history.index[i])
                buyPrice.append(y)
                bought=True
                profitLoss-=qty*y
                print('buying',qty, 'qty at ',history.index[i], 'for', y)
            if  (bought and signalData[history.index[i]]<0):
                sellTime.append(history.index[i])
                sellPrice.append(y)
                bought=False
                profitLoss+=qty*y
                print('selling',qty, 'qty at ',history.index[i],'for',y)
        i+=1
    print('lastprice',lastPrice)
    if bought: # assume sold and calculate price 
        profitLoss+=qty*lastPrice
    return profitLoss, buyTime,buyPrice,sellTime,sellPrice


if __name__ == "__main__":
    register_matplotlib_converters()
    #global variables
    ticker='LABU'
    resampleRate='15min'
    qty=100
    startTime= datetime.strptime('2019-08-7 8:30:00.000000', '%Y-%m-%d %H:%M:%S.%f').astimezone(local_timezone)
    endTime= datetime.strptime('2019-08-9 15:00:00.000000', '%Y-%m-%d %H:%M:%S.%f').astimezone(local_timezone)
    historyStartTime = startTime - timedelta(days=2) # for some reason macd calulation start with some 2 hours offset

    #collect history
    history = get_history_data(ticker, historyStartTime, endTime, resampleRate)
    print (history)
    
    #collect study data
    macd, signalline, signal=macdStudy(history,12,26,9)
    print (signal)
    
    #back test 
    profitLoss, buyTime, buyPrice, sellTime, sellPrice = backTest(history, qty, signal, startTime,endTime)
    print ('profitLoss',profitLoss)
    
    #Plot
    fig,ax=plt.subplots(2,sharex=True)
    ax[0].set_title(ticker)
    ax[0].plot(history.index, history)
    ax[0].scatter(buyTime,buyPrice,marker='o',c='green')
    ax[0].scatter(sellTime,sellPrice,marker='o',c='red')
    ax[1].plot(macd.index, macd, label='MACD', color = 'blue')
    ax[1].plot(signalline.index, signalline, label='Signal Line', color='yellow')
    ax[1].set_xlabel('profitloss of {} qty {} between {} and {}'.format(round(profitLoss,2),qty,startTime,endTime))
    plt.show() 
