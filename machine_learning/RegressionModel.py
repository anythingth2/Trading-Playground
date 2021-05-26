import datetime
import re
import pickle
import numpy as np
import pandas as pd
from .BaseModel import BaseModel

ORIGINAL_ATOMIC_COLUMNS = ['open', 'high', 'low', 'close']
class RegressionModel(BaseModel):
    def __init__(self,  model_path, window_size=48):
        self.window_size = window_size
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        self.lookback_steps = np.arange(window_size)

    def generate_past_atomic_data(self, df, lookback_steps):
        
        base_df = df[['time'] + ORIGINAL_ATOMIC_COLUMNS]
        
        first_datetime = df['time'].min() + pd.Timedelta(hours=max(lookback_steps))
        df = df[df['time'] >= first_datetime]
        for lookback_step in lookback_steps:
            shifting_df = base_df.copy()
            shifting_df['time'] = shifting_df['time'] + pd.Timedelta(hours=lookback_step)
            lookback_columns = [f'p{lookback_step}_{col}' for col in ORIGINAL_ATOMIC_COLUMNS]
            shifting_df.rename(columns=dict(zip(ORIGINAL_ATOMIC_COLUMNS, lookback_columns)), inplace=True)
            
            df = df.merge(shifting_df, how='left', on='time')
        return df

    def get_by_lookback_step(self, df, lookback_step):
        return df.filter(regex=f'p{lookback_step}')
    def get_by_atomic(self, df, atomic_column):
        return df.filter(regex=f'p\d+_{atomic_column}')
    def get_only_atomic(self, df):
        return df.filter(regex=f'p\d+_.')

    def denormalize_target(self, y, df):
        return y * (df['max_close'] - df['min_close']) + df['min_close']

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.generate_past_atomic_data(df, self.lookback_steps)
        df.set_index('time', inplace=True)

        atomic_columns = list(filter(lambda col: re.match('p\d+_.', col), df.columns))

        df['min_close'] = self.get_by_atomic(df, 'close').min(axis=1)
        df['max_close'] = self.get_by_atomic(df, 'close').max(axis=1)

        atomic_df = self.get_only_atomic(df)
        atomic_df = atomic_df.subtract(df['min_close'], axis=0).div(df['max_close'] - df['min_close'], axis=0)
        df[atomic_df.columns] = atomic_df

        self.selected_columns = []
        self.selected_columns += atomic_columns
        return df
    def predict(self, df: pd.DataFrame) -> pd.Series:
        if len(df) < self.window_size:
            return 
        df = self.preprocess(df)

        prediction = self.model.predict(df[self.selected_columns])
        df['prediction'] = self.denormalize_target(prediction, df)

        
        return df['prediction']