import backtrader as bt
import datetime
import time
import numpy as np
import math
import pandas as pd
from machine_learning import RegressionModel

class RegressionIndicator(bt.Indicator):

    lines = ('regression',)

    def __init__(self, model_path, window_size=48):

        self.window_size = window_size
        self.regression_model = RegressionModel(model_path, window_size=window_size)
        self.predict()
        
        self.plotinfo.subplot = False
    def __fetch_ohlc(self):
        datetime_data = self.data.datetime.get(size=self.window_size)
        datetime_data = list(map(bt.num2date, datetime_data))
        datetime_data = pd.to_datetime(datetime_data)
        return pd.DataFrame({
            'time': datetime_data,
            'open': self.data.open.get(size=self.window_size),
            'high': self.data.high.get(size=self.window_size),
            'low': self.data.low.get(size=self.window_size),
            'close': self.data.close.get(size=self.window_size)
        }).sort_values('time')
    
    def predict(self):
        self.predictions = self.regression_model.predict(self.data._dataname.reset_index())

    def next(self):
        datetime = bt.num2date(self.data.datetime[0])
        prediction = self.predictions.get(datetime, default=math.nan)
        
        self.lines.regression[0] = prediction
