import pandas as pd 
import streamlit as st

from ..utils.data_loader import load_dbf

@st.cache_data
def get_suppliers() -> pd.DataFrame:
    df = load_dbf('provedor', columns=[
        'NOM_PROV'
    ], index='CVE_PROV')

    return df