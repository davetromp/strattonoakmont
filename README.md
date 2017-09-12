# README #

Trading bot on the Bittrex api.

### Strategy ###

The bot implements a simple mean reversion and breakout strategy using a simple moving average.

### Backtesting ###

python main.py -c example.config -b example.png

### Running the bot ###

python main.py -c example.config

### Configuration ###

python generate.py

### Installation ###

Requirements file will follow. For now I am sure you will need to install:
* pandas
* matplotlib
* requests

Set your api keys by creating a secret.py file based on the example_secret.py file.

### Steps to process ###

* run 'python generate.py' to generate a set of possible configurations in folder configurations. Variables / currencies / etc can be set in the script.
* run 'python backtest.py' to generate plots of all possible backtests in folder tests and save all results in backtests.csv. Of each market a plot of the best result will be saved in the folder best. The corresponding config file will be saved inthe active folder.
* run 'python runall.py' to run all active configs.

### Additional ###

* run the script run-notebook-server.sh to start a jupyter notebook server. For setup instructions see the comments in the script.
