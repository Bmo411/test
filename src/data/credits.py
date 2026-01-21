import numpy as np
import pandas as pd
import streamlit as st 

from ..utils.data_loader import load_dbf
from ..utils.calc import get_bill_class

#get returns and discounts from database 
@st.cache_data
def get_credits_df() -> pd.DataFrame:
    
    credit_notes = load_dbf('creditos', columns=[
        'CVE_DDA',
        'TIP_NOT',
        'FECHA',
        'DESC_NOTA',
        'NO_CLIENTE',
        'NO_AGENTE',
        'NO_ESTADO',
        'SUBTOTAL', 
        'SALDO',
        'CVE_FACTU',
        'NO_FAC',
        'CVE_MON',
        'TIP_CAM',
        'MES',
        'AÑO',
    ], 
    index='NO_NOTA')

    credit_details = load_dbf('creditod', columns=[
        'CVE_PROD',
        'MEDIDA',
        'CANTIDAD',
        'VALOR_PROD',
        'TOT',
        'UNIDAD', 
        'NEWMED',
    ], 
    index=['NO_NOTA'])

    # Filtrar anticipos sin factura 
    credits = credit_notes[(credit_notes['CVE_DDA'].isin(['D', 'N'])) & (credit_notes['NO_ESTADO'] != 'Cancelada')].copy()
    credits['FACT_ID'] = credits['CVE_FACTU'] + credits['NO_FAC']

    credits = credits.join(credit_details, how='left')

    return credits

# In this function you get the returns of Kilograms and amount
def get_returns_df(credits_df_with_details: pd.DataFrame, products_df: pd.DataFrame) -> pd.DataFrame:

    # Remove dicounts 
    returns_df = credits_df_with_details[credits_df_with_details['TIP_NOT'] == 'Dev. Just.']
    
    #Remove deposit advances
    returns_df = returns_df[returns_df['CVE_PROD'] != 'OTRO-40']
    
    # Get return class 
    products_classes = products_df[['CSE_PROD', 'FACT_PESO']]
    returns_df = returns_df.join(products_classes, on='CVE_PROD', how='left')
    returns_df['PESO_TOTAL_DEV'] = returns_df['CANTIDAD'] * returns_df['FACT_PESO']
    returns_df['DEVOLUCION_MN'] = np.where(returns_df['CVE_MON'] == 1, returns_df['TOT'], returns_df['TOT'] * returns_df['TIP_CAM'])

    return returns_df[['FECHA', 'NO_CLIENTE', 'NO_ESTADO', 'FACT_ID', 'CVE_PROD', 'CANTIDAD', 'UNIDAD', 'CSE_PROD', 'PESO_TOTAL_DEV', 'DEVOLUCION_MN', 'DESC_NOTA']]


def get_discounts_df(credits_df: pd.DataFrame, facturas_with_details_df: pd.DataFrame) -> pd.DataFrame:

    discounts = credits_df[(credits_df['TIP_NOT'] == 'Descuento') | (credits_df['CVE_PROD'] == 'OTRO-40')].copy()
    discounts['CSE_PROD'] = discounts['FACT_ID'].apply(lambda x: get_bill_class(x, facturas_with_details_df))

    # Classify if it is a discount caused by quality or an application of an advance payment
    discounts['CSE_DESCUENTO'] = np.where(discounts['CVE_PROD'] == 'OTRO-40', 'APLICACION ANTICIPO', 'DESCUENTO')
    discounts['MONTO_MN'] = np.where(discounts['CVE_MON'] == 1, discounts['SUBTOTAL'], discounts['SUBTOTAL'] * discounts['TIP_CAM'])

    return discounts[['TIP_NOT', 'CSE_DESCUENTO', 'NO_CLIENTE', 'NO_ESTADO', 'MONTO_MN', 'FACT_ID', 'CSE_PROD', 'FECHA', 'DESC_NOTA']]