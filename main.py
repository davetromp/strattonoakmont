#!/usr/bin/env python

import sys, os
import getopt
from bittrex import bittrex
import requests
import pandas as pd
import time
import datetime
import matplotlib.pyplot as plt
from secret import *


def main(argv):
    """Main function:
    python main.py -b [configfile]
    """
    configfile = ''
    backtestfile = ''
    cache = False
    try:
        opts, args = getopt.getopt(argv, "hc:b:m", ["cfile=", "bfile="])
    except getopt.GetoptError:
        print 'main.py -c <configfile> -b <backtestfile>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'main.py -c <configfile> -b <backtestfile>'
            sys.exit()
        elif opt in ("-c", "--cfile"):
            configfile = arg
        elif opt in ("-b", "--bfile"):
            backtestfile = arg
        elif opt == "-m":
            cache = True
    return configfile, backtestfile, cache


def getBars(market, interval=5, latest=False):
    """Well return historical data from the bittrex api V2.0
    as a dataframe where index is datetime and field returned are
    close, high, low, open and volume."""
    tf = {3600: 'day',
          60: 'hour',
          30: 'thirtyMin',
          5: 'fiveMin',
          1:  'oneMin'}
    # Get prices using PUBLIC API V2.0
    if latest:
        url = 'https://bittrex.com/Api/v2.0/pub/market/GetLatestTick?marketName={}&tickInterval={}'.format(market, tf[
                                                                                                           interval])
    else:
        url = 'https://bittrex.com/Api/v2.0/pub/market/GetTicks?marketName={}&tickInterval={}'.format(market, tf[
                                                                                                      interval])
    response = requests.get(url).json()
    datadf = pd.DataFrame(response['result'])
    datadf['datetime'] = pd.to_datetime(datadf['T'])
    datadf = datadf.set_index('datetime')
    del datadf['T']
    del datadf['BV']
    del datadf['V']
    datadf.columns = ['close', 'high', 'low', 'open']
    return datadf


def getLatestBar(market, interval):
    return getBars(market, interval, True)


def getSharpe(l):
    """returns the sharpe of a ts of pandl"""
    df = pd.DataFrame(data=l)
    df['dd'] = df[0].diff()
    avg = df['dd'].mean()
    std = df['dd'].std()
    # days = 12# figure out using the index which is datetime
    sharpe = (avg / std) #* (365/days) ** 0.5
    return sharpe


def backtest(cache):
    """
    This function will backtest the settings on historical data.
    It will generate a plot of the performance
    """
    if not cache:
        history = getBars(MARKET, TF)
    else:
        cachefile = "cache/{}-{}.csv".format(MARKET,TF)
        try:
            history = pd.read_csv(cachefile, index_col="datetime", parse_dates=True)
        except:
            history = getBars(MARKET, TF)
            history.to_csv(cachefile)
    history['ma'] = history['close'].rolling(MEAN).mean()
    long = False
    entry_price = 0.0
    pl = 0.0
    history['pandl'] = 0.0
    trades = 1
    rtm_perc = (100.0 + RTM_PERCENT) / 100.0
    rtm_perc_max = (100.0 + RTM_PERCENT + LOWER_SIGNAL_BOUND) / 100.0
    bo_perc = (100.0 + BO_PERCENT) / 100.0
    bo_perc_max = (100.0 + BO_PERCENT + UPPER_SIGNAL_BOUND) / 100.0
    exit_perc = (100.0 + EXIT_PERCENT) / 100.0

    ### BEGIN STRATEGY DEFINITION ###
    count = 1
    for i in history.index:
        if count > MEAN:
            # playing revert to mean (RTM)
            if history['ma'][i] * rtm_perc_max < history['close'][i] < history['ma'][i] * rtm_perc and not long and RTM:
                entry = history['close'][i]
                long = True
                history['pandl'][i] = pl
            # playing breakout (BREAKOUT)
            elif history['ma'][i] * bo_perc_max > history['close'][i] > history['ma'][i] * bo_perc and not long and BREAKOUT:
                entry = history['close'][i]
                long = True
                history['pandl'][i] = pl
            elif long and history['close'][i] >= entry * exit_perc:
                exit = entry * exit_perc  # history['close'][i]
                long = False
                pl += ((exit * (1.0 - FEE)) / (entry * (1.0 + FEE)))
                history['pandl'][i] = pl
                trades += 1
            else:
                if long:
                    fpl = (history['close'][-1] * 0.9975 / entry * 1.0025)
                    history['pandl'][i] = pl + fpl
                else:
                    fpl = 0.0
                    history['pandl'][i] = pl + fpl
        count += 1
        ### END STRATEGY DEFINITION ###

    sharpe_ratio = getSharpe(list(history['pandl']))
    days = (len(history) * TF) / (60 * 24)
    fig, ax = plt.subplots(1)
    plt.plot(history['pandl'])
    fig.autofmt_xdate()
    plt.ylabel('cumulative %')
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    # place a text box in upper left in axes coords
    textstr = """{}
    Days: {}
    Trades: {}
    Settings:
    TF = {}
    MEAN = {}
    BREAKOUT = {}
    RTM = {}
    RTM_PERCENT = {}
    BO_PERCENT = {}
    EXIT_PERCENT = {}
    """.format(MARKET,
               days,
               trades,
               TF,
               MEAN,
               BREAKOUT,
               RTM,
               RTM_PERCENT,
               BO_PERCENT,
               EXIT_PERCENT)
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)
    plt.title("BACKTEST {}".format(MARKET))
    plt.savefig(BACKTESTFILE)
    print "{},{},{},{},{},{},{},{},{}".format(MARKET,
                    TF,
                    MEAN,
                    BREAKOUT,
                    RTM,
                    RTM_PERCENT,
                    BO_PERCENT,
                    EXIT_PERCENT,
                    sharpe_ratio)
    # plt.show()


def getMarketPrices(market, interval):
    """Will return a df with timestamp and resampled ohlc prices
    Input market and interval in minutes: 1, 5, 30, 60, 3600"""
    tf = {3600: '3600Min',
          60: '60Min',
          30: '30Min',
          5: '5Min',
          1:  '1Min'}
    history = API.getmarkethistory(MARKET)
    df = pd.DataFrame(history)
    df.index = pd.to_datetime(df['TimeStamp'])
    prices = df['Price'].resample(tf[interval]).ohlc()
    return prices.dropna()


def weAreLong(retries=1, delay=3):
    # Determine we are already long or not
    # if we have balance we are long
    count = 0
    while count < retries:
        balance = API.getbalance(CURRENCY)
        if balance['Balance'] == None or balance['Balance'] == 0.0:
            long = False
        else:
            print "we are long"
            long = True
        count += 1
        if retries != 1:
            time.sleep(delay)
            print "Checking again if we are long"
    return long


def weAreCovered(retries=1, delay=3):
    # Determine we have zero available balance
    # if we have zero avail balance we are covered
    count = 0
    while count < retries:
        balance = API.getbalance(CURRENCY)
        if balance['Available'] == None or balance['Available'] == 0.0:
            covered = True
        else:
            print "we are not covered"
            covered = False
        count += 1
        if retries != 1:
            time.sleep(delay)
            print "Checking again if we are covered"
    return covered


def buySignaled(candle_close_rate, ma, BO_possible):
    mean_diff = candle_close_rate / ma
    print "candle close rate:", candle_close_rate
    print "moving avarage price:", ma
    print "Mean difference:", mean_diff
    rtm_perc = (100.0 - RTM_PERCENT) / 100.0
    bo_perc = (100.0 + BO_PERCENT) / 100.0
    rtm_perc_max = (100.0 - RTM_PERCENT + LOWER_SIGNAL_BOUND) / 100.0
    bo_perc_max = (100.0 + BO_PERCENT + UPPER_SIGNAL_BOUND) / 100.0
    # Price has to above below the mean to trigger a long BO signal.
    if mean_diff >= bo_perc and BREAKOUT and BO_possible:
        print "Break out signal"
        return True
    # Price has to break below the mean to trigger a long RTM signal.
    elif mean_diff <= rtm_perc and RTM:
        print "Reversion to the mean signal"
        return True
    return False


def getBestSellRate(candle_close_rate):
    sellorderbook = pd.DataFrame(API.getorderbook(MARKET, 'sell'))
    if not sellorderbook.empty:
        # filter out price levels that are within our set upper and lower
        # bounds
        lower_buy_price_bound = candle_close_rate * \
            (100.0 - LOWER_BUY_BOUND) / 100.0
        upper_buy_price_bound = candle_close_rate * \
            (100.0 + UPPER_BUY_BOUND) / 100.0
        sellorderbook = sellorderbook[
            sellorderbook['Rate'] <= upper_buy_price_bound]
        sellorderbook = sellorderbook[
            sellorderbook['Rate'] >= lower_buy_price_bound]
        # print sellorderbook
    if not sellorderbook.empty:
        # filter out price levels that can fully fill our order size
        sellorderbook = sellorderbook[sellorderbook['Quantity'] >= QUANTITY]
        # print sellorderbook
    if not sellorderbook.empty:
        best_sell_rate = sellorderbook['Rate'][0]
        # print sellorderbook
        print "best sell rate:", best_sell_rate
        print 'Slippage should be about:', (1 - (candle_close_rate / best_sell_rate)) * 100, "%"
        return best_sell_rate
    print "available prices out of BOUND"


def getPricePoints():
    # get prices and calculte rolling mean.
    df = getMarketPrices(MARKET, TF)
    if len(df) < MEAN:
        df = getBars(MARKET, TF)
        print "Using API 2 for data retreival:", len(df)
    df['ma'] = df['close'].rolling(MEAN).mean()
    candle_close_rate = df['close'][-1]
    ma = df['ma'][-1]
    return candle_close_rate, ma


def trade():

    t = datetime.datetime.now()
    if TF == 1:
        time.sleep((TF * 60) - t.second)
    elif TF == 5 or TF == 30 or TF == 60:
        time.sleep(((TF - t.minute % TF - 1) * 60) + (60 - t.second))
    else:
        print "Timeframe not supported for syncing."
        print "1, 5, 30 and 60 min timeframe is supported for syncing."

    BO_possible = False

    while True:
        start = time.time()

        ### TRADE BEGIN ###
        print ">>>", datetime.datetime.now()
        print "{} on {} min".format(MARKET, TF)
        candle_close_rate, ma = getPricePoints()
        # set a switch for breakout to only be possible if price has been below the ma
        # this is to prevent to get BO signal while starting the bot at price
        # extrems.
        if not BO_possible:
            # make breakout possible if price has moved below ma once
            BO_possible = candle_close_rate <= ma
        we_are_long = weAreLong()
        if not we_are_long and buySignaled(candle_close_rate, ma, BO_possible):
            best_sell_rate = getBestSellRate(candle_close_rate)
            if best_sell_rate is not None:
                buylimit = API.buylimit(MARKET, QUANTITY, best_sell_rate)
                if buylimit['uuid']:
                    print "buylimit succesfully placed"
                    print "Checking position"
                    if weAreLong(3):
                        print "Long position is confirmed"
                        print "Placing sell limit"
                        selllimit = API.selllimit(
                            MARKET, QUANTITY, best_sell_rate * (1.0 + (EXIT_PERCENT / 100.0)))
                        if selllimit['uuid']:
                            print "Sell limit succesfully placed"
                            if weAreCovered(3):
                                open_orders = API.getopenorders(MARKET)
                                print "Open orders"
                                print open_orders
                    else:
                        print "We are not long, need to cancel buy limit"
                        buy_limit_cancel = API.cancel(buylimit['uuid'])
                        print buy_limit_cancel
        elif we_are_long:
            print "do some trade management on our long position"
            print "check if we have a sell limmit in place"
            if not weAreCovered():
                print "we have a long position without a corresponding sell limit"
                print "let's set a sell limit for the available balance at current candle_close_rate and stop the bot"
                # TODO: implement getBestBuyRate
                avail_balance = API.getbalance(CURRENCY)['Available']
                selllimit = API.selllimit(
                    MARKET, avail_balance, candle_close_rate)
            # print "check distance from entry; if over stop, initiate exit and pause trading"
        ### TRADE END ###

        processing_time = time.time() - start
        print "processing_time", processing_time
        # resyncing candle time
        t = datetime.datetime.now()
        if TF == 1:
            time.sleep((TF * 60) - t.second)
        elif TF == 5 or TF == 30 or TF == 60:
            time.sleep(((TF - t.minute % TF - 1) * 60) + (60 - t.second))
        else:
            print "Timeframe not supported for syncing."
            print "1, 5, 30 and 60 min timeframe is supported for syncing."
            print "timing based on processing time"
            time.sleep((TF * 60) - processing_time)


if __name__ == "__main__":
    configfile, BACKTESTFILE, cache = main(sys.argv[1:])
    setting = {}
    with open(configfile) as settings:
        for line in settings:
            if line[0] != '#' and line.strip() != '':
                setting[line.strip().split('=')[0].strip()] = line.strip().split('=')[1].strip()
    TRADE = setting['TRADE']
    CURRENCY = setting['CURRENCY']
    TF = int(setting['TF'])
    MEAN = int(setting['MEAN'])
    BREAKOUT = bool(setting['BREAKOUT'])
    RTM = bool(setting['RTM'])
    RTM_PERCENT = float(setting['RTM_PERCENT'])
    BO_PERCENT = float(setting['BO_PERCENT'])
    EXIT_PERCENT = float(setting['EXIT_PERCENT'])
    QUANTITY = float(setting['QUANTITY'])
    UPPER_SIGNAL_BOUND = float(setting['UPPER_SIGNAL_BOUND'])
    LOWER_SIGNAL_BOUND = float(setting['LOWER_SIGNAL_BOUND'])
    UPPER_BUY_BOUND = float(setting['UPPER_BUY_BOUND'])
    LOWER_BUY_BOUND = float(setting['LOWER_BUY_BOUND'])
    FEE = float(setting['FEE'])
    # Get API key and secret from https://bittrex.com/Account/ManageApiKey
    API = bittrex(KEY, SECRET)
    MARKET = '{0}-{1}'.format(TRADE, CURRENCY)
    if BACKTESTFILE != "":
        if cache:
            backtest(True)
        else:
            backtest(False)
    else:
        print "let's trade"
        trade()
