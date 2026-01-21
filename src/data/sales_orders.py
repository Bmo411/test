import numpy as np
import pandas as pd
import streamlit as st

from ..utils.data_loader import load_dbf

# Get sales orders dataframe 
@st.cache_data
def get_sales_orders(with_details: bool = True) -> pd.DataFrame:
    
    orders = load_dbf('pedidoc', columns=[
        'CVE_CTE',
        'CVE_AGE',
        'F_ALTA_PED', 
        'STATUS',
        'SUBT_PED', 
        'OBSERVA',
        'CVE_MON', 
        'TIP_CAM',
        'MES',
        'AÑO',
        'FECHA_ENT',
        'STATUS2',
        'PESOTOT',
    ], index=['NO_PED'])

    orders = orders[orders['STATUS'] != 'Cancelado']

    if (not with_details):
        cols = ['F_ALTA_PED', 'FECHA_ENT']
        orders[cols] = orders[cols].apply(pd.to_datetime, format='%Y%m%d')

        return orders

    ordersD = load_dbf('pedidod', columns=[
        'CVE_PROD',
        'CSE_PROD',
        'CANT_PROD',
        'VALOR_PROD',
        'FECHA_ENT', 
        'STATUS1',
        'SALDO',
        'UNIDAD',
        'NEW_MED',
        'STAT_PRO',
    ], index='NO_PED')

    # In database, there are times when FECHA_ENT can be NONE
    orders.rename(columns={
        'FECHA_ENT': 'FECHA_ENT_MAIN'
    }, inplace=True)

    orders = orders.join(ordersD, how='left')

    orders['FECHA_ENT'] = orders['FECHA_ENT'].fillna(orders['FECHA_ENT_MAIN'])

    cols = ['F_ALTA_PED', 'FECHA_ENT']
    orders[cols] = orders[cols].apply(pd.to_datetime, format='%Y%m%d')

    return orders