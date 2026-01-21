import streamlit as st

from ..utils.data_loader import load_dbf

# Get clients dataframe
@st.cache_data 
def get_products_df():
    return load_dbf('producto', columns=[
    'CSE_PROD',
    'DESC_PROD',
    'FACT_PESO',
    'UNI_MED',
    'SUB_CSE',
    'SUB_SUBCSE'
    ], index=['CVE_PROD'])