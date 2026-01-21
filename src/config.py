""" GLOBAL VARIABLES AND FUNCTIONS """
import os
import pandas as pd

from typing import Dict

ERP_DB_PATH = r"\\192.168.1.16\vsai\Empresas\LMX24"

YEAR = '2026'

YEAR_OPTIONS = [
    '2024',
    '2025',
    '2026',
]

YEAR_INDEX = 2

MONTHS = {
    "Enero": "01",
    "Febrero": "02",
    "Marzo": "03",
    "Abril": "04",
    "Mayo": "05",
    "Junio": "06",
    "Julio": "07",
    "Agosto": "08",
    "Septiembre": "09",
    "Octubre": "10",
    "Noviembre": "11",
    "Diciembre": "12",
}

MONTH_NAMES = list(MONTHS.keys())

PAGES = ['Facturación', 'Trend de ventas', 'Compras', 'Producción', 'Cartera']

UNITS = ('MN', 'KG')

BUSINESS_UNITS = {
    'RÍGIDOS': ['PS', 'ABS', 'PE', 'PET-G', 'PP', 'MAQUILA'],
    'CORRUGADOS': ['LAMICORR', 'LAMINADOS'],
    'PET': ['PET'],
    'OTROS': ['CARTEA', 'CONVERTING', 'PLA', 'SER', 'LOGISTICA', 'OTRO']
}

MP_CLASSES = ('RESINA', 'MOLIDO')

MP_SUBCLASSES = (
    'ABS', 'PE', 'PET', 'PET-G', 'PP', 'PS'
)

MP_BUSINESS_UNITS = {
    'RÍGIDOS': ['RIGIDO', 'PETG'],
    'CORRUGADOS': ['LAMICORR'],
    'PET': ['PET']
}

AGENTS_TO_FILTER = [9999, 16, 9998, 9997, 2, 3, 4, 5, 6, 8, 12, 13, 14, 16, 17, 18, 20, 21, 23, 24, 25, 27, 28, 29, 30, 31]


def get_table_conn(table_name: str) -> str:
    return os.path.join(ERP_DB_PATH, f"{table_name}.dbf")


def get_business_unit(searched_item: str) -> str | None:
    for key, value in BUSINESS_UNITS.items():
        if searched_item in value:
            return key
    return 'OTROS'

def get_mp_business_unit(searched_item: str) -> str | None:
    for key, value in MP_BUSINESS_UNITS.items():
        if searched_item in value:
            return key
    return 'OTROS'

def get_past_month(curr_month : str, curr_year):
    try:
        index = MONTH_NAMES.index(curr_month)
    except ValueError:
        return None, None
    if (index != 0):
        return MONTH_NAMES[index - 1], curr_year
    else:
        return MONTH_NAMES[-1], str(int(curr_year) - 1)
    
def get_agents_dict(agents_df: pd.DataFrame) -> Dict[str, int]:
    agents_df.drop(AGENTS_TO_FILTER, inplace=True)
    agentsDict = agents_df.reset_index().set_index('NOM_AGE')['CVE_AGE'].to_dict()
    return agentsDict

def get_agents_filtered_list_ids(agents_df: pd.DataFrame, agents_names: list[str] | None) -> list[str]:
    agents_df.drop(AGENTS_TO_FILTER, inplace=True)
    agents_dict = agents_df.reset_index().set_index('NOM_AGE')['CVE_AGE'].to_dict()
    agents_to_filter = [agents_dict[agent_name] for agent_name in agents_names]

    return agents_to_filter
