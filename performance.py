#!/usr/bin/env python

import sys
import numpy as np
from bittrex import bittrex
import pandas as pd
import matplotlib.pyplot as plt
from secret import *


def getPerformance(market):
    API = bittrex(KEY, SECRET)
    orderhistory = API.getorderhistory(market, 20)
    df = pd.DataFrame(orderhistory)
    df = df.sort_values('Closed')
    # df = df [3:]
    # print df
    buys = []
    solds = []
    bands =[]
    bs =0.0
    buy = 0.0
    sold = 0.0
    for i in df.index:
        if df['OrderType'][i] == 'LIMIT_BUY':
            buy += df['PricePerUnit'][i] * df['Quantity'][i]
            bs -= df['PricePerUnit'][i] * df['Quantity'][i]
        else:
            sold += df['PricePerUnit'][i] * df['Quantity'][i]
            bs += df['PricePerUnit'][i] * df['Quantity'][i]
        buys.append(buy)
        solds.append(sold)
        bands.append(bs)
    # print buys
    buy_avg = np.mean(buys)
    # print buy_avg
    # print solds
    sell_avg = np.mean(solds)
    # print sell_avg
    print "Difference between average sells and buys"
    print sell_avg - buy_avg
    # plt.plot(pd.to_datetime(df['Closed']), buys)
    # plt.plot(pd.to_datetime(df['Closed']), solds)
    plt.plot(pd.to_datetime(df['Closed']), bands)
    plt.show()


if __name__ == "__main__":
    try:
        getPerformance(sys.argv[1])
    except:
        print "please provide market"
        print "python performance.py <MARKET>"
