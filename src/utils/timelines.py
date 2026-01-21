import pandas as pd
import numpy as np

from typing import Literal

def create_timeline_df(df: pd.DataFrame, date_col: str) -> pd.Series:

    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    df.set_index(date_col, inplace=True)

    return df

def create_timeline_by_month(df: pd.DataFrame, date_col: str) -> pd.Series:
    pass