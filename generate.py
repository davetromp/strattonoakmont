import os

print "remove all config files from folder configs"
for f in os.listdir("configs/"):
    os.remove("configs/{}".format(f))

print "generating new configfiles in folder configs"
trades = ['BTC']
for trade in trades:
    currencies = ['LTC', 'ETH', 'BCC', 'XRP', 'XMR', 'DASH', 'NEO', 'OMG', 'STRAT', 'ETC',
                  'APX', 'RISE', 'MCO', 'LSK', 'XVG', 'NAV', 'TRIG', 'PAY', 'QTUM', 'MTL', 'BAT', 'ADX']
    for currency in currencies:
        timeframes = [5]
        for tf in timeframes:
            means = [8, 20]
            for mean in means:
                rtm_percs = [2.0, 3.0, 5.0]
                for rtm_perc in rtm_percs:
                    bo_percs = [1.0]
                    for bo_perc in bo_percs:
                        exit_percs = [1.0, 5.0, 10.0]
                        for exit_perc in exit_percs:
                            for stop_perc in [5.0, 10.0, 15.0]:
                                config = """
                                TRADE = {}
                                CURRENCY = {}
                                TF = {}
                                MEAN = {}
                                BREAKOUT = True
                                RTM = True
                                RTM_PERCENT = {}
                                BO_PERCENT = {}
                                EXIT_PERCENT = {}
                                QUANTITY = 1
                                BTC_QUANTITY = 0.005
                                LOWER_SIGNAL_BOUND = 1.0
                                UPPER_SIGNAL_BOUND = 1.0
                                UPPER_BUY_BOUND = 1.0
                                LOWER_BUY_BOUND = 5.0
                                FEE = 0.25
                                STOP_PERC = {}
                                """.format(trade,
                                           currency,
                                           tf,
                                           mean,
                                           rtm_perc,
                                           bo_perc,
                                           exit_perc,
                                           stop_perc)
                                with open("configs/{}-{}_{}_{}_True_True_{}_{}_{}_{}.config".format(trade,
                                                                                             currency,
                                                                                             tf,
                                                                                             mean,
                                                                                             rtm_perc,
                                                                                             bo_perc,
                                                                                             exit_perc,
                                                                                             stop_perc), 'w') as configfile:
                                    configfile.write(config)
