from dbfread import DBF 
import pandas as pd 
import streamlit as st 

from src.config import get_table_conn

@st.cache_data 
def load_dbf(table_name: str, columns: list = None, index:list = None) -> pd.DataFrame:
    dbf = DBF(get_table_conn(table_name))
    df = pd.DataFrame(iter(dbf))

    if index:
        df.set_index(index, inplace=True)
    if columns: 
        df = df[columns]
    
    return df

