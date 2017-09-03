#!/usr/bin/env python

import sys
import numpy as np
from bittrex import bittrex
import pandas as pd
import matplotlib.pyplot as plt
from secret import *


def getPerformance(market):
    try:
        API = bittrex(KEY, SECRET)
        orderhistory = API.getorderhistory(market, 20)
        if orderhistory:
            df = pd.DataFrame(orderhistory)
            df = df.sort_values('Closed')
            diffs = []
            buy = 0.0
            sell = 0.0
            diffs.append(0.0)
            for i in df.index:
                if df['OrderType'][i] == 'LIMIT_BUY':
                    buy += df['PricePerUnit'][i] * df['Quantity'][i]
                else:
                    sell += df['PricePerUnit'][i] * df['Quantity'][i]
                diffs.append(sell - buy)
            print "Difference between cumulative sells and buys"
            print sell / buy
            plt.plot(diffs)
            plt.axhline(y=0.0, color='r', linestyle='-')
            plt.title("Difference between cumulative sells and buys over time")
            plt.ylabel("Difference %")
            plt.xlabel("Limit orders")
            plt.show()
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
