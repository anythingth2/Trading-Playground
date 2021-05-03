import ccxt
from itertools import product
import datetime
import pandas as pd
from pathlib import Path
import tqdm
exchange = ccxt.binance()
exchange.load_markets()

symbols = ['BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'BNB/USDT']
timeframes = ['1d', '1h']
start_datetime = datetime.datetime(2019, 1, 1)

output_dir = Path('dataset')
output_dir.mkdir(exist_ok=True)
for symbol, timeframe in tqdm.tqdm(product(symbols, timeframes)):

    data = exchange.fetch_ohlcv(
        symbol, timeframe, since=exchange.parse8601(start_datetime))
    df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'tick_volume'])
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    
    df.to_csv(output_dir / f'{symbol.replace("/", "")}_{timeframe}.csv', index=False)