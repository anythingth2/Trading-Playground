# %%
from datetime import datetime

import MetaTrader5 as mt5

import config
# %%

if not mt5.initialize(config.PATH,
                      login=config.USERNAME,
                      password=config.PASSWORD,
                      server=config.SERVER
                      ):
    print("initialize() failed")
    mt5.shutdown()
# %%


# request connection status and parameters
print(mt5.terminal_info())
# get data on MetaTrader 5 version
print(mt5.version())
# %%
# request 1000 ticks from EURAUD
euraud_ticks = mt5.copy_ticks_from("EURAUDm", datetime(
    2020, 1, 28, 13), 1000, mt5.COPY_TICKS_ALL)
# request ticks from AUDUSD within 2019.04.01 13:00 - 2019.04.02 13:00
audusd_ticks = mt5.copy_ticks_range("AUDUSD", datetime(
    2020, 1, 27, 13), datetime(2020, 1, 28, 13), mt5.COPY_TICKS_ALL)

# get bars from different symbols in a number of ways
eurusd_rates = mt5.copy_rates_from(
    "EURUSD", mt5.TIMEFRAME_M1, datetime(2020, 1, 28, 13), 1000)
eurgbp_rates = mt5.copy_rates_from_pos("EURGBP", mt5.TIMEFRAME_M1, 0, 1000)
eurcad_rates = mt5.copy_rates_range("EURCAD", mt5.TIMEFRAME_M1, datetime(
    2020, 1, 27, 13), datetime(2020, 1, 28, 13))


# %%
print(euraud_ticks)

# %%
mt5.copy_ticks_range("GBPUSDm", datetime(
    2020, 1, 27, 13), datetime(2020, 1, 28, 13), mt5.COPY_TICKS_ALL)

# %%
