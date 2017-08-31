import os

print "remove all config files from folder configs"
for f in os.listdir("configs/"):
    os.remove("configs/{}".format(f))

print "generating new configfiles in folder configs"
trades = ['BTC']
for trade in trades:
    currencies = ['LTC', 'ETH', 'BCC', 'XRP', 'XMR', 'DASH', 'NEO', 'OMG', 'STRAT', 'ETC']
    for currency in currencies:
        timeframes = [1, 5, 30]
        for tf in timeframes:
            means = [8, 20]
            for mean in means:
                breakout = [True, False]
                for bo in breakout:
                    meanreversion = [True, False]
                    if bo == False:
                        meanreversion = [True]
                    for mr in meanreversion:
                        if mr == True:
                            rtm_percs = [2.0, 3.0, 5.0]
                        else:
                            rtm_percs = [2.0]
                        for rtm_perc in rtm_percs:
                            if bo == True:
                                bo_percs = [1.0, 2.0, 3.0]
                            else:
                                bo_percs = [1.0]
                            for bo_perc in bo_percs:
                                exit_percs = [1.0, 2.0, 3.0, 4.0, 5.0]
                                for exit_perc in exit_percs:
                                    config = """
                                    TRADE = {}
                                    CURRENCY = {}
                                    TF = {}
                                    MEAN = {}
                                    BREAKOUT = {}
                                    RTM = {}
                                    RTM_PERCENT = {}
                                    BO_PERCENT = {}
                                    EXIT_PERCENT = {}
                                    QUANTITY = 1
                                    LOWER_SIGNAL_BOUND = 1.0
                                    UPPER_SIGNAL_BOUND = 1.0
                                    UPPER_BUY_BOUND = 1.0
                                    LOWER_BUY_BOUND = 5.0
                                    FEE = 0.25
                                    """.format(trade,
                                               currency,
                                               tf,
                                               mean,
                                               bo,
                                               mr,
                                               rtm_perc,
                                               bo_perc,
                                               exit_perc)
                                    with open("configs/{}-{}_{}_{}_{}_{}_{}_{}_{}.config".format(trade,
                                               currency,
                                               tf,
                                               mean,
                                               bo,
                                               mr,
                                               rtm_perc,
                                               bo_perc,
                                               exit_perc), 'w') as configfile:
                                        configfile.write(config)
