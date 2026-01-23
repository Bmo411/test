import os
import sys
import streamlit as st

# Patch st.error to ensure we see the error
def print_error(msg):
    print(f"ERROR: {msg}")

st.error = print_error

# Set environment variable for testing
os.environ["ERP_DB_PATH"] = "https://lap.blueberrieslab.com/files"

# Add current directory to path so we can import src
sys.path.append(os.getcwd())

from src.utils.data_loader import load_dbf
from src.config import ERP_DB_PATH

print(f"Testing connection to: {ERP_DB_PATH}")

try:
    # Try to load 'agentes' as it is small
    print("Attempting to load 'agentes.dbf'...")
    df = load_dbf('agentes')
    if not df.empty:
        print("Successfully loaded 'agentes.dbf'!")
        print(f"Columns: {df.columns.tolist()}")
        print(f"Rows: {len(df)}")
    else:
        print("Loaded dataframe is empty.")
except Exception as e:
    print(f"Failed to load: {e}")
