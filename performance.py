#!/usr/bin/env python

import sys
import numpy as np
from bittrex import bittrex
import pandas as pd
import matplotlib.pyplot as plt
from secret import *


def getPerformance(market, plot = True):
    try:
        API = bittrex(KEY, SECRET)
        orderhistory = API.getorderhistory(market, 20)
        if orderhistory:
            df = pd.DataFrame(orderhistory)
            df = df.sort_values('Closed')
            df = df[df['Closed'] >= '2017-09-04']
            df = df.reset_index()
            if df['OrderType'][0] == "LIMIT_SELL":
                df = df [1:]
            diffs = []
            buy = 0.0
            sell = 0.0
            diffs.append(0.0)
            for i in df.index:
                if df['OrderType'][i] == 'LIMIT_BUY':
                    buy += df['PricePerUnit'][i] * df['Quantity'][i]
                else:
                    sell += df['PricePerUnit'][i] * df['Quantity'][i]
                    diffs.append( ( (sell - buy) / buy ) * 100.0)
            if plot:
                print "Difference between cumulative sells and buys"
                print diffs[-1], "%"
                plt.plot(diffs)
                plt.axhline(y=0.0, color='r', linestyle='-')
                plt.title("Difference between cumulative sells and buys over time")
                plt.ylabel("Difference %")
                plt.xlabel("SELL Limit orders")
                plt.show()
            else:
                return diffs
        else:
            print "There is no order history yet."
    except Exception as e:
        print "Failed at getPerformance:", str(e)


if __name__ == "__main__":
    try:
        getPerformance(sys.argv[1])
    except:
        print "please provide market"
        print "python performance.py <MARKET>"
