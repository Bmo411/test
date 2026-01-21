import pandas as pd 
import streamlit as st

from ..utils.data_loader import load_dbf

@st.cache_data
def get_pos(with_details: bool = True) -> pd.DataFrame:
    # po table 
    po = load_dbf('comprapc', columns=[
        'F_ALTA_PED',
        'STATUS',
        'TOTAL_PED',
        'SUBT_PED',
        'FECH_ENT',
        'CVE_MON',
        'TIP_CAM',
        'MES',
        'AÑO',
        'LUGAR',
        'STATUS_AUT',
    ], index='NO_PEDC')

    # po details 
    pod = load_dbf('comprapd', columns=[
        'CVE_PROD',
        'CSE_PROD',
        'CANT_PROD',
        'VALOR_PROD',
        'STATUS1',
        'CVE_PROV', 
        'SALDO',
        'F_ENT', 
        'UNIDAD', 
        'NEW_MED',
    ], index='NO_PEDC')

    po['FECH_ENT'] = pd.to_datetime(po['FECH_ENT'], errors='coerce')

    if with_details:
        df = pod.join(po, how='left')
    else:
        df = po

    df = df[df['STATUS'] != 'Cancelado']

    return df