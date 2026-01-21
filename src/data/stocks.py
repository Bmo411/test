import pandas as pd 
import streamlit as st

from ..utils.data_loader import load_dbf

@st.cache_data
def get_existencias() -> pd.DataFrame:
    df = load_dbf('existe', columns=[
        'CVE_PROD',
        'NEW_MED',
        'LUGAR', 
        'EXISTENCIA',
        'FECH_UMOD', 
        'LOTE', 
        'FECH_LOTE',
        'COSTO_PROM',
        'COSTUEPEPS'
    ])

    df = df[df['EXISTENCIA'] != 0]

    return df