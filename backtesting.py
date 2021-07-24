import argparse

import backtrader as bt
from backtrader_plotting import Bokeh, OptBrowser
from backtrader_plotting.schemes import Tradimo, Blackly
import matplotlib.pylab as pylab
import pandas as pd
import yaml
import importlib
import datetime
import logging
from pathlib import Path
from util import OrderHistoryTracker, order_history_tracker
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


def init_logging():
    log_root_dir = Path('logs')
    log_root_dir.mkdir(exist_ok=True)

    log_dir = log_root_dir / Path(args.config_path).stem
    log_dir.mkdir(exist_ok=True)

    log_path = log_dir / f'{datetime.datetime.now()}.log'
    logging.basicConfig(
        filename=str(log_path),
        filemode='w',
        level=logging.DEBUG)

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(console)
    logging.getLogger('matplotlib.font_manager').disabled = True
    return log_path


def set_figsize(width, height):
    pylab.rcParams['figure.figsize'] = width, height


def load_dataset():

    df = pd.read_csv(config['dataset'])
    df['time'] = pd.to_datetime(df['time'])
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)
    if 'real_volume' in df.columns:
        df.drop(columns=['real_volume'], inplace=True)
    df.rename(columns={'tick_volume': 'volume'}, inplace=True)
    if config.get('start_date') is not None:
        df = df.loc[config.get('start_date'):]
    if config.get('end_date') is not None:
        df = df.loc[: config.get('end_date')]
    return df


config = parse_config()
log_path = init_logging()
order_history_tracker = OrderHistoryTracker(
    log_path.parent / f'{log_path.stem}.csv',)

logging.info('import', config['dataset'])
df = load_dataset()
logging.info(df.head())
data_feed = bt.feeds.PandasData(dataname=df)

cerebro = bt.Cerebro(stdstats=False)
cerebro.broker.set_coc(True)
logging.info('init cash', config['broker']['init_cash'])
cerebro.broker.set_cash(config['broker']['init_cash'])

logging.info('default stake', config['sizer']['default_stake'])
cerebro.addsizer(bt.sizers.SizerFix, stake=config['sizer']['default_stake'])

cerebro.adddata(data_feed)

cerebro.addobserver(bt.observers.Broker)
cerebro.addobserver(bt.observers.BuySell, barplot=True)
cerebro.addobserver(bt.observers.Trades)
cerebro.addobserver(bt.observers.TimeReturn)

cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)
cerebro.addanalyzer(bt.analyzers.PyFolio)
for strategy_config in config['strategies']:
    logging.info('Add strategy', strategy_config['name'])
    logging.info('params', strategy_config['params'])
    cerebro.addstrategy(
        strategy=strategy_config['strategy'],
        # tracker=order_history_tracker,
        **strategy_config['params'])


cerebro.run()
ending_value = cerebro.broker.getvalue()
print('ending value', ending_value)
if config.get('plot'):
    set_figsize(10, 8)
    # b = Bokeh(style='bar', plot_mode='single', scheme=Blackly())
    # cerebro.plot(b)
    cerebro.plot(iplot=True, style='bar')
