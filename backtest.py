import os

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
os.system("""echo "MARKET,TF,MEAN,BREAKOUT,RTM,RTM_PERCENT,BO_PERCENT,EXIT_PERCENT,sharpe_ratio" >> backtests.csv""")
files = os.listdir("configs/")
count = 1
for f in files:
    configfile = "configs/" + f
    backtestfile = "tests/" + f[:-6] + ".png"
    os.system("python main.py -c {} -b {} -m >> backtests.csv".format(
        configfile,
        backtestfile
    ))
    print count
    count += 1
