import streamlit as st

from ..utils.data_loader import load_dbf

# Get agents dataframe
@st.cache_data 
def get_agents_df(just_name: bool = False):
    agents = load_dbf('agentes', columns=['NOM_AGE', 'FALTA_AGE', 'AREA_AGE', 'EMAIL_AGE'], index=['CVE_AGE'])

    if just_name:
        return agents[['NOM_AGE']]
    
    return agents