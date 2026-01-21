import pandas as pd
import numpy as np

from ..config import get_past_month, MONTHS
from typing import Tuple

# Get the class of a bill with different products
def get_bill_class(fact_id: str, bills_df: pd.DataFrame) -> str: 
    if (fact_id == ''):
        return 'OTRO'
    bill = bills_df.loc[[fact_id]]
    class_list = bill['CSE_PROD'].unique()

    if (len(class_list) > 0):
        return class_list[0]
    else:
        return class_list[0]
    

def get_past_and_current_month_df(df: pd.DataFrame, date_column: str, current_month: str, curr_year) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Return two dataframes on with the current month data, and other with the past month"""

    past_month, corr_year = get_past_month(current_month)

    past_month = MONTHS[past_month]
    month = MONTHS[current_month]
    
    # TODO -> VERIFY date_column is type datetime
    
    df = df[
        ((df[date_column].dt.month == int(month)) & 
        (df[date_column].dt.year == int(curr_year)))
        |
        ((df[date_column].dt.month == int(past_month)) & 
        (df[date_column].dt.year == int(corr_year)))
    ]

    last_month_mask = (df[date_column].dt.month == int(past_month)) & (df[date_column].dt.year == int(corr_year)) 

    last_month_df = df.loc[last_month_mask]
    this_month_df = df.loc[~last_month_mask]

    return this_month_df, last_month_df


    
def get_fact_by_col(facts_df: pd.DataFrame, col: str) -> pd.DataFrame:
    facts_df['FACTURADO'] = facts_df['SUBT_PROD'] * np.where(facts_df['CVE_MON'] != 1, facts_df['TIP_CAM'], 1)
    facts_df['FACTURADO_KG'] = facts_df['CANT_SURT'] * facts_df['FACT_PESO']
    grouped_df = facts_df.groupby(col)[['FACTURADO', 'FACTURADO_KG']].sum()
    return grouped_df


def get_so_by_col(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Return the sales orders by class with average price"""
    df = df.copy()
    df['KG_PROD'] = df['CANT_PROD'] * df['FACT_PESO']
    df['KG_PROD_SALDO'] = np.where(df['STATUS'] != 'Surtido', df['SALDO'], 0) * df['FACT_PESO']
    df['VALOR_PROD_MN'] = np.where(df['CVE_MON'] == 1, df['VALOR_PROD'], df['VALOR_PROD'] * df['TIP_CAM'])
    df['MONTO_PROD'] = df['VALOR_PROD_MN'] * df['CANT_PROD'] 
    df['MONTO_PROD_SALDO'] = df['VALOR_PROD_MN'] * np.where(df['STATUS'] != 'Surtido', df['SALDO'], 0)
    grouped_df = df.groupby(col)[['KG_PROD', 'KG_PROD_SALDO', 'MONTO_PROD', 'MONTO_PROD_SALDO']].sum()
    grouped_df['PRECIO_PROMEDIO'] = grouped_df['MONTO_PROD'] / grouped_df['KG_PROD']
    grouped_df['PRECIO_PROMEDIO_SALDO'] = grouped_df['MONTO_PROD_SALDO'] / grouped_df['KG_PROD_SALDO']
    

    return grouped_df