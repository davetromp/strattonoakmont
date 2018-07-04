# README #

Trading bot on the Bittrex api. 

20180704
This some code I had sitting in my archives. I used it to trade live, but it did not make me any money.
Use at yout own risk. I provide this code for educational purposes only.

### Strategy ###

The bot implements a simple mean reversion and breakout strategy using a simple moving average.

### Backtesting ###

```python main.py -c example.config -b example.png```
This will backtest one specific configuration and saves a plot of the backtest performance to a .png file.

```python  backtest.py```


### Running the bot ###

```python main.py -c example.config```
This will run one specific configuration.

python runall.py
This will run all configurations found in the active folder.

### Configuration ###

python generate.py
This will generate multiple cofiguration files within the configs folder, which can then be used to backtest or forward trade.

### Installation ###

Requirements file will follow. For now I am sure you will need to install:
* pandas
* matplotlib
* requests

Set your api keys by creating a secret.py file based on the example_secret.py file.

### Steps to process ###

* run 'python generate.py' to generate a set of possible configurations in folder configurations. Variables / currencies / etc can be set in the script.
* run 'python backtest.py' to generate plots of all possible backtests in folder tests and save all results in backtests.csv. Of each market a plot of the best result will be saved in the folder best. The corresponding config file will be saved in the active folder.
* run 'python runall.py' to run all active configs.

The idea is to regurally run backtest to get new best configurations based on past performance and by doing so keep up with changing markets.

### Additional ###

* run the script run-notebook-server.sh to start a jupyter notebook server. For setup instructions see the comments in the script.

### Contact ###
dave at davetromp.net