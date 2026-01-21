import pandas as pd 
import streamlit as st

from ..utils.data_loader import load_dbf

@st.cache_data 
def oc_facs(with_details: bool = True) -> pd.DataFrame: 
    oc_fac = load_dbf('comprafc', columns=[
        'NO_FACC',
        'CVE_PROV',
        'STATUS_FAC',
        'SALDO_FAC',
        'LUGAR',
        'CVE_MON',
        'TIP_CAM',
        'SALDO_FAC2',
        'FECH_VENCI',
    ], index='NO_FACC')

    oc_facd = load_dbf('comprafd', columns=[
        'NO_FACC', 
        'CVE_PROV',
        'CSE_PRDO',
        'CVE_PROD',
        'CANT_SURT',
        'VALOR_PROD',
        'SUBT_PROD',
        'UNIDAD',
        'NEW_MED'
    ], index='NO_FACC')

    if with_details:
        df = oc_facd.join(oc_fac, how='left')
    else: 
        df = oc_fac

    df = df[df['STATUS'] != 'Cancelada']
    return df



