import argparse

import backtrader as bt
import matplotlib.pylab as pylab
import pandas as pd
import yaml
import importlib

# from strategy import GoldenCrossStrategy, GridTradingStrategy

argparser = argparse.ArgumentParser()
argparser.add_argument('config_path')
args = argparser.parse_args()


def parse_config():
    with open(args.config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    for strategy_config in config['strategies']:
        strategy = getattr(importlib.import_module(
            f"strategy.{strategy_config['strategy']}"), strategy_config['strategy'])
        strategy_config['strategy'] = strategy

    return config


config = parse_config()


def set_figsize(width, height):
    pylab.rcParams['figure.figsize'] = width, height


def load_dataset():
    
    df = pd.read_csv(config['dataset'])
    df['time'] = pd.to_datetime(df['time'])
    df.set_index('time', inplace=True)
    if 'real_volume' in df.columns:
        df.drop(columns=['real_volume'], inplace=True)
    df.rename(columns={'tick_volume': 'volume'}, inplace=True)
    if config['start_date'] is not None:
        df = df.loc[config['start_date']:]
    if config['end_date'] is not None:
        df = df.loc[: config['end_date']]
    return df


print('import', config['dataset'])
df = load_dataset()
print(df.head())
data_feed = bt.feeds.PandasData(dataname=df)

cerebro = bt.Cerebro()

print('init cash', config['broker']['init_cash'])
cerebro.broker.set_cash(config['broker']['init_cash'])

print('default stake', config['sizer']['default_stake'])
cerebro.addsizer(bt.sizers.SizerFix, stake=1000)

cerebro.adddata(data_feed)

for strategy_config in config['strategies']:
    print('Add strategy', strategy_config['name'])
    print('params', strategy_config['params'])
    cerebro.addstrategy(
        strategy=strategy_config['strategy'], **strategy_config['params'])


cerebro.run()

set_figsize(10, 8)
cerebro.plot(iplot=True, style='bar')
