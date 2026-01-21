import streamlit as st

from ..utils.data_loader import load_dbf

# Get clients dataframe
@st.cache_data 
def get_clients_df():
    return load_dbf('clientes', columns=['NOM_CTE'], index=['CVE_CTE'])