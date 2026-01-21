import pandas as pd
import streamlit as st

from ..utils.data_loader import load_dbf


# Get invoices data frames
@st.cache_data 
def get_facturas_df(with_details: bool = True):
    facturas = load_dbf('facturac', columns=[
        'CVE_FACTU',
        'NO_FAC',
        'CVE_CTE',
        'FALTA_FAC',
        'STATUS_FAC',
        'CVE_MON',
        'TIP_CAM',
        'PESOTOT',
        'CVE_AGE',
        'F_PAGO',
        'SUBT_FAC',
        'TOTAL_FAC',
        'DESCUENTO',
        'SALDO_FAC',
        'SALDO_FAC2',
        'MES',
        'AÑO',
    ])

    # Create indexes based on code and and number 
    facturas['FACT_ID'] = facturas['CVE_FACTU'] + facturas['NO_FAC']
    facturas.set_index('FACT_ID', inplace=True)
    # Drops columns 
    facturas.drop(['CVE_FACTU', 'NO_FAC'], axis=1, inplace=True)

    if with_details:
        facturasD = load_dbf('facturad', columns=[
            'CVE_FACTU',
            'NO_FAC',
            'CSE_PROD',
            'CVE_PROD',
            'VALOR_PROD',
            'CANT_SURT',
            'SUBT_PROD',
            'DESCU_PROD',
        ])
        
        # Create indexes based on code and and number 
        facturasD['FACT_ID'] = facturasD['CVE_FACTU'] + facturasD['NO_FAC']
        facturasD.set_index('FACT_ID', inplace=True)
        # Drop columns not needed
        facturasD.drop(['CVE_FACTU', 'NO_FAC'], axis=1, inplace=True)

        # Join dataframes in one 
        facts = facturasD.join(facturas)
    
    else: 
        facts = facturas

    # Delete "Cancelada" bills
    facts.drop(facts[facts['STATUS_FAC'] == 'Cancelada'].index, inplace=True)

    # Transform date columns of obj to datetime col
    facts['FALTA_FAC'] = pd.to_datetime(facts['FALTA_FAC'])
    facts['F_PAGO'] = pd.to_datetime(facts['F_PAGO'])

    # Delete traspaso de materiales 
    facts.drop(facts[facts['CVE_AGE'] == 9999].index, inplace=True)

    return facts




