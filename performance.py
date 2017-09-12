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
            df.index = pd.to_datetime(df['Closed'])
            df['sell'] = 0.0
            df['buy'] = 0.0
            for i in df.index:
                if df['OrderType'][i] == 'LIMIT_BUY':
                    df['buy'][i] = df['PricePerUnit'][i] * df['Quantity'][i]
                else:
                    df['sell'][i] = df['PricePerUnit'][i] * df['Quantity'][i]
            df['diffs'] = (df['sell'] - df['buy']).cumsum()
            if plot:
                print "Difference between cumulative sells and buys"
                # print "{} %".format(df['diffs'][-1])
                fig, ax = plt.subplots()
                plt.plot(df['diffs'])
                fig.autofmt_xdate()
                plt.axhline(y=0.0, color='r', linestyle='-')
                plt.title("Difference between cumulative sells and buys over time")
                plt.ylabel("Difference %")
                plt.xlabel("Time")
                plt.show()
            else:
                return df
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
