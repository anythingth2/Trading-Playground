import pandas as pd
class BaseModel:
    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        pass
    def predict(self, df: pd.DataFrame) -> float:
        pass
        