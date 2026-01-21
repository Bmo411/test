import pandas as pd 
import numpy as np

from typing import Literal

""" GET TREND OF THE PEDIDOD TABLE (MUST INCLUDE DETAILS)"""
def get_trend(df : pd.DataFrame, unit: Literal['kg', "mn"] = "mn") -> float:
    
    int_unit = unit.strip().lower() 
    if  int_unit == 'kg':
        df['INT_COL'] = df['FACT_PESO'] * df['CANT_PROD']
    else:
        df = df.copy()
        df['INT_COL'] = df['CANT_PROD'] * df['VALOR_PROD'] * np.where(df['CVE_MON'] != 1, df['TIP_CAM'], 1 )

    return df['INT_COL'].sum()


def get_supplied_of_orders(df: pd.DataFrame, unit: Literal['kg', 'mn', '%'] = '%') -> float:

    supplied_df = df[df['STATUS'] == 'Surtido'].copy()

    if unit.strip().lower() == 'kg':
        supplied = get_trend(supplied_df, 'kg')
    else:
        trend = get_trend(df, 'mn')
        supplied = get_trend(supplied_df, 'mn')

    if unit == '%':
        return supplied / trend
    else:
        return supplied