import pandas as pd
import matplotlib.pylab as pylab
import backtrader as bt
from strategy import GoldenCrossStrategy
def set_figsize(width, height):
    pylab.rcParams['figure.figsize'] = width, height

def load_dataset(path):
    df = pd.read_csv(path)
    df['time'] = pd.to_datetime(df['time'])
    df.set_index('time', inplace=True)
    df.drop(columns=['real_volume'], inplace=True)
    df.rename(columns={'tick_volume': 'volume'}, inplace=True)
    return df

df = load_dataset('dataset/AUDUSDm_d1.csv')
# df = df.loc[: '2020-07-01']
data_feed = bt.feeds.PandasData(dataname=df)

cerebro = bt.Cerebro()
cerebro.broker.set_cash(10000.0)
cerebro.addsizer(bt.sizers.SizerFix, stake=1000)
cerebro.adddata(data_feed)
cerebro.addstrategy(GoldenCrossStrategy)


cerebro.run()

set_figsize(10, 8)
cerebro.plot(iplot=True, style='bar')