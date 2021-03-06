#!/usr/bin/env python

import gc
import sys
import os
import logging
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
        logging.info('main.py -c <configfile> -b <backtestfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            logging.info('main.py -c <configfile> -b <backtestfile>')
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
    try:
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
        if BACKTESTFILE != "":
            return datadf
        return datadf.tail(MEAN)
    except Exception as e:
        logging.error("failed at getBars")
        logging.error(str(e))


def getLatestBar(market, interval):
    return getBars(market, interval, True)


def getSharpe(l, days):
    """returns the sharpe of a ts of pandl"""
    df = pd.DataFrame(data=l)
    df['dd'] = df[0].diff()
    avg = df['dd'].mean()
    std = df['dd'].std()
    try:
        sharpe = (avg / std) * (365 / days) ** 0.5
        return sharpe
    except:
        return None


def backtest(cache):
    """
    This function will backtest the settings on historical data.
    It will generate a plot of the performance
    """
    if not cache:
        history = getBars(MARKET, TF)
    else:
        cachefile = "cache/{}-{}.csv".format(MARKET, TF)
        try:
            history = pd.read_csv(
                cachefile, index_col="datetime", parse_dates=True)
        except:
            history = getBars(MARKET, TF)
            history.to_csv(cachefile)
    history['ma'] = history['close'].rolling(MEAN).mean()
    weAreLong = False
    PRICE_DIPPED = False

    entry = 0.0
    exit = None
    pl = 0.0
    history['pandl'] = 0.0
    trades = 1

    ### BEGIN STRATEGY DEFINITION ###
    count = 1

    for i in history.index:
        candle_close_rate = history['ma'][i]
        ma = history['close'][i]
        if count > MEAN:
            # playing revert to mean (RTM)
            if not weAreLong and buySignaled(candle_close_rate, ma, PRICE_DIPPED):
                entry = candle_close_rate
                exit = candle_close_rate * (1.0 + (EXIT_PERCENT / 100.0))
                stop = candle_close_rate * (1.0 - (STOP_PERC / 100.0))
                weAreLong = True
                history['pandl'][i] = pl
            elif weAreLong and history['high'][i] >= exit:
                weAreLong = False
                pl += (((exit - entry) / entry) * 100.0 ) - (2.0 * FEE)
                history['pandl'][i] = pl
                trades += 1
            elif weAreLong and candle_close_rate <= stop:
                weAreLong = False
                pl += (((candle_close_rate - entry) / entry) * 100.0 ) - (2.0 * FEE)
                history['pandl'][i] = pl
                trades += 1
            else:
                if weAreLong:
                    # fpl = ((history['close'][i] * (1.0 - FEE)) - (entry * (1.0 + FEE)))
                    # fpl = ( (history['close'][i] * (100.0 - FEE)) - (entry * (100.0 + FEE)) ) / 100.0
                    fpl = ((candle_close_rate - entry) / entry) * 100.0
                    history['pandl'][i] = pl + fpl
                else:
                    fpl = 0.0
                    history['pandl'][i] = pl + fpl
        count += 1
        if candle_close_rate <= ma:
            PRICE_DIPPED = True
        else:
            PRICE_DIPPED = False
        ### END STRATEGY DEFINITION ###

    days = (len(history) * TF) / (60 * 24)
    sharpe_ratio = getSharpe(list(history['pandl']), days)
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
    EXIT_PERCENT = {},
    STOP = {}
    Sharpe = {}
    """.format(MARKET,
               days,
               trades,
               TF,
               MEAN,
               BREAKOUT,
               RTM,
               RTM_PERCENT,
               BO_PERCENT,
               EXIT_PERCENT,
               STOP_PERC,
               sharpe_ratio)
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)
    plt.title("BACKTEST {}".format(MARKET))
    plt.savefig(BACKTESTFILE)
    print("{},{},{},{},{},{},{},{},{},{},{},{}".format(days,
                    trades,
                    MARKET,
                    TF,
                    MEAN,
                    BREAKOUT,
                    RTM,
                    RTM_PERCENT,
                    BO_PERCENT,
                    EXIT_PERCENT,
                    STOP_PERC,
                    sharpe_ratio))
    # plt.show()


def getMarketPrices(market, interval):
    """Will return a df with timestamp and resampled ohlc prices
    Input market and interval in minutes: 1, 5, 30, 60, 3600"""
    try:
        tf = {3600: '3600Min',
              60: '60Min',
              30: '30Min',
              5: '5Min',
              1:  '1Min'}
        history = API.getmarkethistory(MARKET)
        df = pd.DataFrame(history)
        df.index = pd.to_datetime(df['TimeStamp'])
        prices = df['Price'].resample(tf[interval]).ohlc()
        if BACKTESTFILE != "":
            return prices.dropna()
        return prices.dropna().tail(MEAN)
    except Exception as e:
        logging.error("failed at getMarketPrices")
        logging.error(str(e))

def weAreLong(retries=1, delay=3):
    try:
        # Determine we are already long or not
        # if we have balance we are long
        count = 0
        while count < retries:
            balance = API.getbalance(CURRENCY)
            if not (balance['Balance'] == None or balance['Balance'] == 0.0):
                logging.info("we are long")
                return True
            count += 1
            if retries != 1:
                time.sleep(delay)
                logging.info("Checking again if we are long")
        return False
    except Exception as e:
        logging.error("failed at weAreLong")
        logging.error(str(e))

def weAreCovered(retries=1, delay=3):
    try:
        # Determine we have zero available balance
        # if we have zero avail balance we are covered
        count = 0
        while count < retries:
            balance = API.getbalance(CURRENCY)
            if balance['Available'] == None or balance['Available'] == 0.0:
                logging.info("we are covered")
                return True
            else:
                logging.info("we are not covered")
            count += 1
            if retries != 1:
                time.sleep(delay)
                logging.info("Checking again if we are covered")
        return False
    except Exception as e:
        logging.error("failed at weAreCovered")
        logging.error(str(e))


def buySignaled(candle_close_rate, ma, BO_possible):
    try:
        mean_diff = candle_close_rate / ma
        # print "candle close rate:", candle_close_rate
        # print "moving avarage price:", ma
        # print "Mean difference:", mean_diff
        rtm_perc = (100.0 - RTM_PERCENT) / 100.0
        bo_perc = (100.0 + BO_PERCENT) / 100.0
        rtm_perc_max = (100.0 - RTM_PERCENT + LOWER_SIGNAL_BOUND) / 100.0
        bo_perc_max = (100.0 + BO_PERCENT + UPPER_SIGNAL_BOUND) / 100.0
        # Price has to above below the mean to trigger a long BO signal.
        if mean_diff >= bo_perc and BREAKOUT and BO_possible:
            logging.info("Break out signal")
            return True
        # Price has to break below the mean to trigger a long RTM signal.
        elif mean_diff <= rtm_perc and RTM:
            logging.info("Reversion to the mean signal")
            return True
        return False
    except Exception as e:
        logging.error("failed at buySignaled")
        logging.error(str(e))


def getBestSellRate(candle_close_rate):
    try:
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
            # logging.info(sellorderbook)
        if not sellorderbook.empty:
            # filter out price levels that can fully fill our order size
            sellorderbook = sellorderbook[sellorderbook['Quantity'] >= QUANTITY]
            logging.info(sellorderbook)
        if not sellorderbook.empty:
            sellorderbook = sellorderbook.reset_index()
            best_sell_rate = sellorderbook['Rate'][0]
            # logging.info(sellorderbook)
            logging.info("best sell rate: {}".format(best_sell_rate))
            logging.info('Slippage should be about: {}%'.format( str(1 - (candle_close_rate / best_sell_rate)) * 100))
            return best_sell_rate
        logging.info("available prices out of BOUND")
    except Exception as e:
        logging.error("failed at getBestSellRate")
        logging.error(str(e))


def getBestBuyRate(candle_close_rate):
    try:
        buyorderbook = pd.DataFrame(API.getorderbook(MARKET, 'buy'))
        if not buyorderbook.empty:
            # filter out price levels that are within our set upper and lower
            # bounds
            lower_sell_price_bound = candle_close_rate * \
                (100.0 - LOWER_SELL_BOUND) / 100.0
            upper_sell_price_bound = candle_close_rate * \
                (100.0 + UPPER_SELL_BOUND) / 100.0
            buyorderbook = buyorderbook[
                buyorderbook['Rate'] <= upper_sell_price_bound]
            buyorderbook = buyorderbook[
                buyorderbook['Rate'] >= lower_sell_price_bound]
            # logging.info(buyorderbook)
        if not buyorderbook.empty:
            # filter out price levels that can fully fill our order size
            buyorderbook = buyorderbook[buyorderbook['Quantity'] >= QUANTITY]
            # logging.info(buyorderbook)
        if not buyorderbook.empty:
            buyorderbook = buyorderbook.reset_index()
            best_buy_rate = buyorderbook['Rate'][0]
            logging.info("best buy rate: {}".format(best_buy_rate))
            logging.info('Slippage should be about: {}%'.format( str(1 - (candle_close_rate / best_buy_rate) ) * 100) )
            return best_buy_rate
        logging.info("available prices out of BOUND")
    except Exception as e:
        logging.error("failed at getBestBuyRate")
        logging.error(str(e))


def getPricePoints():
    try:
        # get prices and calculte rolling mean.
        df = getMarketPrices(MARKET, TF)
        if len(df) < MEAN:
            df = getBars(MARKET, TF)
            logging.info("Using API 2 for data retrieval: {}".format(len(df)))
        df['ma'] = df['close'].rolling(MEAN).mean()
        candle_close_rate = df['close'][-1]
        ma = df['ma'][-1]
        return candle_close_rate, ma
    except Exception as e:
        logging.error("failed at getPricePoints")
        logging.error(str(e))


def checkStop(candle_close_rate):
    try:
        logging.info("Check if stop level is hit.")
        open_orders = API.getopenorders(MARKET)
        if open_orders and open_orders[0]['OrderType'] == 'LIMIT_SELL':
            sell_limit_price = open_orders[0]['Limit']
            entry_price = sell_limit_price / (1.0 + (EXIT_PERCENT / 100.0))
            stop_rate = entry_price * (1.0 - (STOP_PERC / 100.0))
            if candle_close_rate <= stop_rate:
                logging.info("price went below our stop rate")
                logging.info("cancelling current sell limit")
                API.cancel(open_orders[0]['OrderUuid'])
                time.sleep(3)
                logging.info("placing a new sell limit at stop level")
                avail_balance = API.getbalance(CURRENCY)['Available']
                bestprice = getBestBuyRate(candle_close_rate)
                if not bestprice:
                    bestprice = candle_close_rate
                selllimit = API.selllimit(
                    MARKET, avail_balance, bestprice)
                if 'uuid' in selllimit:
                    logging.info("selllimit placed. Price: {}, Units: {}".format(bestprice, avail_balance))
                else:
                    logging.info("selllimit failed")
    except Exception as e:
        logging.error("failed at checkStop")
        logging.error(str(e))


def enterLong(candle_close_rate, QUANTITY):
    try:
        best_sell_rate = getBestSellRate(candle_close_rate)
        if best_sell_rate is not None:
            logging.info("Placing buy limit for {} tokens of market {} at {} for a total of {} BTC".format(
                QUANTITY,
                MARKET,
                best_sell_rate,
                QUANTITY * best_sell_rate
            ))
            if BTC_QUANTITY:
                QUANTITY = BTC_QUANTITY / candle_close_rate
            buylimit = API.buylimit(MARKET, QUANTITY, best_sell_rate)
            logging.info(buylimit)
            if 'uuid' in buylimit:
                logging.info("buylimit succesfully placed")

                logging.info("Checking position")
                if weAreLong(3):
                    entry = candle_close_rate
                    logging.info("Long position is confirmed")
                    logging.info("Placing sell limit")
                    try:
                        selllimit = API.selllimit(
                            MARKET, QUANTITY, best_sell_rate * (1.0 + (EXIT_PERCENT / 100.0)))
                    except:
                        logging.info("failed at enterLong while placing sell limit")
                        selllimit = {}
                    if 'uuid' in selllimit:
                        logging.info("Sell limit succesfully placed")
                        if weAreCovered(3):
                            open_orders = API.getopenorders(MARKET)
                            logging.info("Open orders")
                            logging.info(open_orders)
                    else:
                        logging.info("no selluuid")
                else:
                    logging.info("We are not long, need to cancel buy limit")
                    try:
                        buy_limit_cancel = API.cancel(buylimit['uuid'])
                        logging.info(buy_limit_cancel)
                    except:
                        logging.error("failed at enterLong while cancelling buylimit order")
            else:
                logging.info("could not get uuid for buylimit")
                logging.info("could be tst buy failed. If not we will place sell limit at next candle close")
    except Exception as e:
        logging.error("failed at enterLong")
        logging.error(str(e))


def manageTrade(candle_close_rate):
    try:
        logging.info("Do some trade management on a long position")
        if not weAreCovered():
            logging.info("we have a long position without a corresponding sell limit")
            logging.info("let's set a sell limit for the available balance at target level")
            orderhistory = API.getorderhistory(MARKET)
            if orderhistory and orderhistory[0]['OrderType'] == 'LIMIT_BUY':
                avail_balance = API.getbalance(CURRENCY)['Available']
                buy_limit_price = orderhistory[0]['Limit']
                targetprice = buy_limit_price * (1.0 + (EXIT_PERCENT / 100.0))
                sellimit = API.selllimit(
                    MARKET, avail_balance, targetprice)
            else:
                logging.info("get out at best current price")
                bestprice = getBestBuyRate(candle_close_rate)
                sellimit = API.selllimit(
                    MARKET, avail_balance, bestprice)
        checkStop(candle_close_rate)
    except Exception as e:
        logging.error("failed at manageTrade")
        logging.error(str(e))

def trade():
    t = datetime.datetime.now()
    if TF == 1:
        time.sleep((TF * 60) - t.second)
    elif TF == 5 or TF == 30 or TF == 60:
        time.sleep(((TF - t.minute % TF - 1) * 60) + (60 - t.second))
    else:
        logging.info("Timeframe not supported for syncing.")
        logging.info("1, 5, 30 and 60 min timeframe is supported for syncing.")
    entry = None
    selluuid = None
    PRICE_DIPPED = False
    # set a switch for breakout to only be possible if price has dipped below ma
    # this is to prevent to get BO signal while at price extremes.
    while True:
        start = time.time()
        ### TRADE BEGIN ###
        logging.info(">>>")
        try:
            print ">>> {} {}".format(MARKET,datetime.datetime.now())
            logging.info("{} on {} min".format(MARKET, TF))
            candle_close_rate, ma = getPricePoints()
            we_are_long = weAreLong()
            if not we_are_long and buySignaled(candle_close_rate, ma, PRICE_DIPPED):
                enterLong(candle_close_rate, QUANTITY)
            elif we_are_long:
                manageTrade(candle_close_rate)
            if candle_close_rate < ma:
                PRICE_DIPPED = True
            else:
                PRICE_DIPPED = False
            ### TRADE END ###
            processing_time = time.time() - start
            logging.info("processing_time: {}".format(processing_time))
            # resyncing candle time
            t = datetime.datetime.now()
            if TF == 1:
                time.sleep((TF * 60) - t.second)
            elif TF == 5 or TF == 30 or TF == 60:
                time.sleep(((TF - t.minute % TF - 1) * 60) + (60 - t.second))
            else:
                logging.info("Timeframe not supported for syncing.")
                logging.info("1, 5, 30 and 60 min timeframe is supported for syncing.")
                logging.info("timing based on processing time")
                time.sleep((TF * 60) - processing_time)
        except Exception as e:
            logging.error("Something went wrong in the trade loop")
            logging.error(str(e))
            processing_time = time.time() - start
            time.sleep((TF * 60) - processing_time)
        # do some garbage collection
        gc.collect()


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
    BTC_QUANTITY = float(setting['BTC_QUANTITY'])
    UPPER_SIGNAL_BOUND = float(setting['UPPER_SIGNAL_BOUND'])
    LOWER_SIGNAL_BOUND = float(setting['LOWER_SIGNAL_BOUND'])
    UPPER_BUY_BOUND = float(setting['UPPER_BUY_BOUND'])
    LOWER_BUY_BOUND = float(setting['LOWER_BUY_BOUND'])
    UPPER_SELL_BOUND = float(setting['UPPER_SELL_BOUND'])
    LOWER_SELL_BOUND = float(setting['LOWER_SELL_BOUND'])
    FEE = float(setting['FEE'])
    STOP_PERC = float(setting['STOP_PERC'])
    # Get API key and secret from https://bittrex.com/Account/ManageApiKey
    API = bittrex(KEY, SECRET)
    MARKET = '{0}-{1}'.format(TRADE, CURRENCY)
    logging.basicConfig(filename="logs/{}.log".format(MARKET),
                        format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)
    if BACKTESTFILE != "":
        if cache:
            backtest(True)
        else:
            backtest(False)
    else:
        logging.info("let's trade {}".format(MARKET))
        print ("let's trade {}".format(MARKET))
        trade()
