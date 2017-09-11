import os, sys
import pandas as pd
from shutil import copyfile


def runTests():
    print "remove the backtests.csv file"
    os.remove("backtests.csv")

    print "remove all backtest result files from folder tests"
    for ff in os.listdir("tests/"):
        os.remove("tests/{}".format(ff))

    print "remove all cached data files"
    for fff in os.listdir("cache/"):
        os.remove("cache/{}".format(fff))

    print "running backtests aginst all config files in folder configs"
    # print "MARKET,TF,MEAN,BREAKOUT,RTM,RTM_PERCENT,BO_PERCENT,EXIT_PERCENT,sharpe_ratio"
    os.system("""echo "MARKET,TF,MEAN,BREAKOUT,RTM,RTM_PERCENT,BO_PERCENT,EXIT_PERCENT,STOP_PERC,sharpe_ratio" >> backtests.csv""")
    files = os.listdir("configs/")
    count = 1
    for f in files:
        configfile = "configs/" + f
        backtestfile = "tests/" + f[:-6] + "png"
        os.system("python main.py -c {} -b {} -m >> backtests.csv".format(
            configfile,
            backtestfile
        ))
        print count
        count += 1

def bestOnes():
    df = pd.read_csv("backtests.csv")
    markets = df['MARKET'].unique()[:-1]
    dfmm = []
    dfm = {}
    for market in markets:
        dfm[market] = df[df['MARKET'] == market]
        dfm[market] = dfm[market][dfm[market]['sharpe_ratio'] == max(dfm[market]['sharpe_ratio'])]
        dfm[market] = dfm[market].reset_index()#.ix[0]
        dfm[market] = dfm[market][dfm[market].index == 0]
        dfmm.append(dfm[market])
    return pd.concat(dfmm).reset_index()


if __name__ == "__main__":
    try:
        runTests()
        best = bestOnes()
        for i in best.index:
            try:
                # base = "_".join(list(best.ix[i])[2:-1])
                base = ""
                for elem in list(best.ix[i])[2:-1]:
                    base += "_" + str(elem)
                base = base[1:]
                configfile = base + ".config"
                try:
                    copyfile("configs/" + configfile, "active/" +configfile.split("_")[0]+".config")
                except Exception as e:
                    print str(e)
                plotfile = base + ".png"
                try:
                    copyfile("tests/" + plotfile, "best/" +plotfile)
                except Exception as e:
                    print str(e)
            except Exception as e:
                print str(e)
    except KeyboardInterrupt:
        sys.exit()
