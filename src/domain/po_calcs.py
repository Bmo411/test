import pandas as pd
import numpy as np

from ..data.productos import get_products_df
from ..data.purchase_orders import get_pos
from ..data.suppliers import get_suppliers

from ..utils.dates_calculator import range_of_months_to_dates

from ..config import get_mp_business_unit

"""
FUNCIONES A REALIZAR:

-> PARA GRAFICO DE LÍNEAS 
    -> TIMESERIES POR RESINA DE PRECIOS POR KILOGRAMOS
        - PARAMS: RESINA, INTERVAL (MONTH, DAY), RANGE=DEFAULT 1 YEAR

    -> Calculo de promedio de costo de resina (filtrado por resinas y de cuánto tiempo)
        - PARAMS: LISTA DE RESINAS, SI RESINA O MOLIDO, DE LOS ÚLTIMOS X CANTIDAD DE TIEMPO 

    -> Pivot table de provedor y precio promedio por resinas 
    -> 
"""

def _weighted_avg(group, avg_col, weight_col):
    d = group[avg_col]
    w = group[weight_col]
    try:
        return (d * w).sum() / w.sum()
    except ZeroDivisionError:
        return 0

# The business unit filter just works for classes MOLIDO and RESINA
def transform_dataframe(base_month: str, 
                        base_year: str, 
                        po_class: str = None, 
                        business_units: list[str] = [], 
                        mp_subclasses: list[str] = None, 
                        range_of_months: int = None) -> pd.DataFrame:

    pos = get_pos()
    suppliers = get_suppliers()
    products = get_products_df()

    if range_of_months:
        start_date, end_date = range_of_months_to_dates(base_month, base_year, range_of_months)

        pos = pos[pos['FECH_ENT'].between(start_date, end_date)]

    if po_class:
        pos = pos[pos['CSE_PROD'] == (po_class)]

    products.drop(columns=['CSE_PROD'], inplace=True)
    
    main_df = pos.join(suppliers, on='CVE_PROV', how='left')
    main_df = main_df.join(products, on='CVE_PROD')

    main_df['BUSINESS_UNIT'] = main_df['SUB_SUBCSE'].apply(lambda x: get_mp_business_unit(x))

    if business_units and len(business_units) > 0:
        main_df = main_df[main_df['BUSINESS_UNIT'].isin(business_units)]

    # Filter specific type of resins
    if mp_subclasses and len(mp_subclasses) > 0:
        main_df = main_df[main_df['SUB_CSE'].isin(mp_subclasses)]

    # Verify the dataframe 
    if main_df.empty:
        return main_df

    # Remove FACT_PESO values of 0 
    main_df.loc[main_df['FACT_PESO'] == 0, 'FACT_PESO'] = 1
    
    main_df['VALOR_MN'] = main_df['VALOR_PROD'] * np.where(main_df['CVE_MON'] != 1, main_df['TIP_CAM'], 1)
    main_df['CANT_KG'] = main_df['CANT_PROD'] * main_df['FACT_PESO']

    return main_df


def get_prices_by_client_and_resin(base_month, 
                                   base_year, 
                                   po_class: str = None, 
                                   business_units: list[str] = [], 
                                   range_of_months: int = None, 
                                   mp_subclasses: list[str] = None, 
                                   just_by_resin: bool = False) -> pd.DataFrame:

    df = transform_dataframe(base_month=base_month, 
                             base_year=base_year, 
                             po_class=po_class, 
                             business_units=business_units, 
                             mp_subclasses=mp_subclasses,
                             range_of_months=range_of_months)
    
    if df.empty:
        return df

    df['TOT_PROD_MN'] = df['CANT_PROD'] * df['VALOR_MN']
    
    if (just_by_resin):
        df = df.groupby(['SUB_CSE'])[['CANT_KG', 'TOT_PROD_MN']].sum()

    else:
        df = df.groupby(['SUB_CSE', 'NOM_PROV'])[['CANT_KG', 'TOT_PROD_MN']].sum()

    df['VALOR_KG_MN'] = df['TOT_PROD_MN'] / df['CANT_KG']
    df = df.reset_index()

    if (just_by_resin):
        return df
    else:
        pivot_df = df.pivot(index='NOM_PROV', columns='SUB_CSE', values='VALOR_KG_MN')
        return pivot_df
    


def get_to_be_supplied_orders_by_resin(base_month, 
                                       base_year, 
                                       po_class: str = None, 
                                       business_units: list[str] = [], 
                                       mp_subclasses: list[str] = None): 
    
    df = transform_dataframe(base_month=base_month, 
                             base_year=base_year, 
                             po_class=po_class, 
                             business_units=business_units,
                             mp_subclasses=mp_subclasses)
    
    if df.empty:
        return df
    
    df = df[df['STATUS'] != 'Surtido']
    df['SALDO_KG'] = df['SALDO'] * np.where(df['UNI_MED'] == 'KG', 1, df['FACT_PESO'])
    df['TOT_SALDO_MN'] = df['SALDO'] * df['VALOR_MN']
    df = df.groupby('SUB_CSE')[['SALDO_KG', 'TOT_SALDO_MN']].sum()
    df['COSTO_PROM_OC'] = df['TOT_SALDO_MN'] / df['SALDO_KG']
    df.reset_index(inplace=True)
    return df


def get_po_resins_prices_series(base_month: str, 
                                base_year: str, 
                                po_class: str = None, 
                                business_units: list[str] = [], 
                                range_of_months: int = None, 
                                mp_subclasses: list[str] = None) -> list[tuple[pd.Series, str]]:
    
    df = transform_dataframe(base_month=base_month,
                            base_year=base_year,
                            po_class=po_class,
                            business_units=business_units,
                            mp_subclasses=mp_subclasses,
                            range_of_months=range_of_months)
    
    if df.empty:
        return None
    
    df['FECH_ENT'] = pd.to_datetime(df['FECH_ENT'], errors='coerce')
    df['MES_ENT'] = df['FECH_ENT'].dt.to_period('M')

    grouped_df = (
        df.groupby(['SUB_CSE', 'MES_ENT'])[['VALOR_MN', 'CANT_KG']]
        .apply(lambda x: (x['VALOR_MN'] * x['CANT_KG']).sum() / x['CANT_KG'].sum())
        .reset_index(name='PRECIO_KG')
    )
    grouped_df['MES_ENT'] = grouped_df['MES_ENT'].dt.to_timestamp()

    series = []
    for cls, data in grouped_df.groupby('SUB_CSE'):
        curr_serie = data[['MES_ENT', 'PRECIO_KG']].set_index('MES_ENT')['PRECIO_KG']
        series.append((curr_serie, cls))
    
    return series

def get_month_savings(base_month: str, 
                      base_year: str, 
                      po_class: str = None, 
                      business_units: list[str] = [], 
                      mp_subclasses: list[str] = None) -> float:

    df = transform_dataframe(base_month=base_month,
                             base_year=base_year, 
                             po_class=po_class,
                             business_units=business_units,
                             mp_subclasses=mp_subclasses,
                             range_of_months=2)
    
    if df.empty:
        return []
    
    df['FECH_ENT'] = pd.to_datetime(df['FECH_ENT'], errors='coerce')
    df['MES_ENT'] = df['FECH_ENT'].dt.to_period('M')

    current_month = df['MES_ENT'].max()
    prev_month = current_month - 1

    df_current = df[df['MES_ENT'] == current_month].copy()
    df_prev = df[df['MES_ENT'] == prev_month].copy()

    if (df_prev.empty or df_current.empty):
        print('Sin órdenes de compra en ambos meses')
        savings = int(0)
    
    else:
        avg_prices_prev = df_prev.groupby('SUB_CSE')[['VALOR_MN', 'CANT_KG']].apply(_weighted_avg, 'VALOR_MN', 'CANT_KG').rename(
            'VALOR_PREV'
        )

        
        avg_prices_current = df_current.groupby('SUB_CSE')[['VALOR_MN', 'CANT_KG']].apply(
            lambda g: pd.Series({
                'VALOR_CURR': _weighted_avg(g, 'VALOR_MN', 'CANT_KG'),
                'CURR_KG': g['CANT_KG'].sum()
            })
        )


        new_df = avg_prices_current.join(avg_prices_prev, how='inner')
        new_df['AHORRO_SOBRECOSTO'] = (new_df['VALOR_PREV'] - new_df['VALOR_CURR']) * new_df['CURR_KG']
        savings = new_df['AHORRO_SOBRECOSTO'].sum()

        return savings
    