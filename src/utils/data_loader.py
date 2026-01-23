from dbfread import DBF
import pandas as pd
import streamlit as st
import requests
import tempfile
import os

from src.config import get_table_conn

@st.cache_data
def load_dbf(table_name: str, columns: list = None, index:list = None) -> pd.DataFrame:
    conn_path = get_table_conn(table_name)

    if conn_path.startswith("http"):
        try:
            # Add timeout to avoid hanging indefinitely
            response = requests.get(conn_path, timeout=10)
            response.raise_for_status()

            # Create a localized temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".dbf") as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name

            # Read DBF from temp file
            dbf = DBF(tmp_path)
            df = pd.DataFrame(iter(dbf))

        except Exception as e:
            st.error(f"Error loading {table_name}: {e}")
            return pd.DataFrame()
        finally:
            # Clean up temp file
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
    else:
        dbf = DBF(conn_path)
        df = pd.DataFrame(iter(dbf))

    if index:
        df.set_index(index, inplace=True)
    if columns:
        # Ensure all requested columns exist, ignoring missing ones to prevent errors if schema mismatch
        available_columns = [c for c in columns if c in df.columns]
        df = df[available_columns]

    return df
