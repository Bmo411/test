import pandas as pd
import streamlit as st

from ..utils.data_loader import load_dbf

@st.cache_data
def get_res_ops_df():
    results = load_dbf('ordproc', columns=[
        'NO_ORDP',
        'FECH_ORDP',
        'CVE_COPR',
        'REN_COPR',
        'STATUS',
        'CTO_UNIT',
        'NO_OPRO',
        'DATOEST4',
        'NEW_COPR',
        'UNCRES'
    ])

    # DROP RESULTS CANCELED
    results.drop(results[results['STATUS'] == 'Cancelada'].index, inplace=True)

    # Make fech_ordp a datetime column
    results['FECH_ORDP'] = pd.to_datetime(results['FECH_ORDP'])

    return results