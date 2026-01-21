import pandas as pd
import numpy as np
from typing import Literal

from ..config import get_business_unit, get_mp_business_unit
from ..utils.formatting import to_currency

from ..data.stocks import get_existencias
from ..data.productos import get_products_df


"""
OPERACIONES QUE DEBE DE HACER EXISTENCIA 

    EXISTENCIA EN KILOGRAMOS, VALOR Y COSTO PROMEDIO DE RESINAS
    - Filtrar periodo de tiempo 
    - Filtrar unidad de negocio
"""

def transform_dataframe(po_classes: list[str] = [], 
                        stock_of: Literal['PT', 'MP'] = None, 
                        business_units: list[str] = [],
                        sub_classes: list[str] = None) -> pd.DataFrame:

    stocks = get_existencias()
    products = get_products_df()

    if len(po_classes) > 0:
        products = products[products['CSE_PROD'].isin(po_classes)]

    # For filtering business unit, there must be an stock_of_param
    if stock_of == 'MP':
        products['BU'] = products['SUB_SUBCSE'].apply(lambda x: get_mp_business_unit(x))
        
    else: 
        products['BU'] = products['CSE_PROD'].apply(lambda x: get_business_unit(x))

    if (len(business_units) > 0):
        products = products[products['BU'].isin(business_units)]
    
    if sub_classes and len(sub_classes) > 0:
        products = products[products['SUB_CSE'].isin(sub_classes)]

    df = products.merge(stocks, how='inner', on='CVE_PROD').copy()

    df['EXI_KG'] = df['EXISTENCIA'] * np.where(df['UNI_MED'] == 'KG', 1, df['FACT_PESO']) 

    return df
    

def get_mp_stocks_with_value_and_avg_cost(po_classes= list[str], business_units: list[str] = [], sub_classes: list[str] = None) -> pd.DataFrame:

    df = transform_dataframe(po_classes=po_classes, stock_of='MP', business_units=business_units, sub_classes=sub_classes)
    df['VALOR_TOT'] = df['EXISTENCIA'] * df['COSTO_PROM']

    df = df.groupby(['SUB_CSE']).agg(
            EXI_KG=('EXI_KG', 'sum'),
            VALOR_TOT=('VALOR_TOT', 'sum'),
            COSTO_MIN_EXI=('COSTO_PROM', 'min'),
            COSTO_MAX_EXI=('COSTO_PROM', 'max'),
        )
    df['VALOR_PROM'] = df['VALOR_TOT'] / df['EXI_KG']
    df = df.reset_index()

    return df


def render_styled_df(po_classes: list[str] = [],
                     stock_of: Literal['PT', 'MP'] = None, 
                     business_units: list[str] = [],
                     sub_classes: list[str] = None) -> pd.DataFrame:
    
    df = transform_dataframe(po_classes=po_classes,
                             stock_of=stock_of,
                             business_units=business_units,
                             sub_classes=sub_classes)
    
    df = df[['SUB_CSE', 'CVE_PROD', 'DESC_PROD', 'NEW_MED', 'EXISTENCIA',
             'UNI_MED', 'COSTO_PROM', 'LUGAR','LOTE', 'FECH_UMOD', 'FECH_LOTE']]
    
    df['COSTO_PROM'] = df['COSTO_PROM'].apply(lambda x: to_currency(x))
    df.sort_values(['SUB_CSE', 'CVE_PROD'], ascending=True, inplace=True)

    df.set_index('CVE_PROD', inplace=True)
    
    df.rename(columns={
        'SUB_CSE': 'RESINA',
        'CVE_PROD': 'CLAVE',
        'DESC_PROD': 'DESCRIPCION',
        'NEW_MED': 'ATRIBUTO',
        'UNI_MED': 'UNIDAD',
        'COSTO_PROM': 'COSTO',
        'FECH_UMOD': 'ULTIMO MOVIMIENTO',
        'FECH_LOTE': 'FECHA LOTE',
    }, inplace=True)
    
    
    return df