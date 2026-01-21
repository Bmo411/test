import pandas as pd
import numpy as np

from typing import Literal

from ..config import get_agents_filtered_list_ids, get_business_unit

from ..data.sales_orders import get_sales_orders
from ..data.productos import get_products_df
from ..data.clientes import get_clients_df
from ..data.agents import get_agents_df

from ..utils.dates_calculator import filter_dataframe_by_range_of_months
from ..utils.timelines import create_timeline_df
from ..utils.formatting import to_currency, to_kg

from ..domain.billing_calcs import get_net_billing_by_agent, get_net_billing_by_col


# In the params, or df is filtered by status or range of time
# For date filtering, the function must get a month and a year
def transform_so_df(base_month: str = None,
                    base_year: str = None,
                    range_of_months: str = None,
                    pt_classes: list[str] = None,
                    order_status: Literal['Por Surtir', 'Surtido'] | None = None,
                    agents_list: list[str] | None = None) -> pd.DataFrame:
    
    df = get_sales_orders(with_details=True)

    if (base_month and base_year and range_of_months):

        df = filter_dataframe_by_range_of_months(df,
                                                 'FECHA_ENT',
                                                 base_month, 
                                                 base_year,
                                                 range_of_months)
    
    if order_status == 'Por Surtir':
        df = df[df['STATUS1']  == '']
    elif order_status == 'Surtido':
        df = df[df['STATUS1'] != '']

    agents_df = get_agents_df(just_name=True)
    clients = get_clients_df()

    if agents_list and len(agents_list) > 0:
        agents_to_filter = get_agents_filtered_list_ids(agents_df, agents_list)
        df = df[df['CVE_AGE'].isin(agents_to_filter)]

    # Filter sales orders by business units
    if pt_classes and len(pt_classes) > 0:
        df = df[df['CSE_PROD'].isin(pt_classes)]
    
    products_df = get_products_df()
    products_df = products_df[['DESC_PROD', 'FACT_PESO', 'UNI_MED']]

    df = df.join(products_df, on='CVE_PROD', how='left')
    df = df.join(agents_df, on='CVE_AGE', how='left')
    df = df.join(clients, on='CVE_CTE', how='left')

    df['SUBT_PROD_MN'] = df['CANT_PROD'] * df['VALOR_PROD'] * np.where(df['CVE_MON'] == 1, 1, df['TIP_CAM'])
    df['SALDO_PROD_MN'] = np.where(df['STATUS1'] == '', df['SALDO'], 0) * df['VALOR_PROD'] * np.where(df['CVE_MON'] == 1, 1, df['TIP_CAM'])

    # Deshabilitado para que de igual que el SAI, (Hay algunos productos con factor de 0 y unidades KG)
    # df['SALDO_KG'] = np.where(df['STATUS1'] == '', df['SALDO'], 0) * np.where(df['UNI_MED'] == 'KG', 1, df['FACT_PESO'])
    # df['TOT_KG'] = df['CANT_PROD'] * np.where(df['UNI_MED'] == 'KG', 1, df['FACT_PESO'])
    df['TOT_KG'] = df['CANT_PROD'] * df['FACT_PESO']
    df['SALDO_KG'] = np.where(df['STATUS1'] == '', df['SALDO'], 0) * df['FACT_PESO']
    

    return df

def get_sales_orders_amount(base_month: str,
                            base_year: str,
                            pt_classes: list[str] = None,
                            agents_list: list[str] = None,
                            range_of_months: int = 1,
                            unit: Literal['MN', 'KG'] = 'MN') -> float:
    df = transform_so_df(
        base_month=base_month,
        base_year=base_year,
        range_of_months=range_of_months,
        pt_classes=pt_classes,
        agents_list=agents_list
    )

    if unit == 'KG':
        result = df['TOT_KG'].sum()
    else:
        result = df['SUBT_PROD_MN'].sum()

    return result


def to_be_supplied_orders_until_base_month(base_month: str,
                                           base_year: str,
                                           pt_classes: list[str] = None,
                                           agents_list: list[str] = None,
                                           amount_of_past_months: int = 6) -> pd.DataFrame:
    
    df = transform_so_df(pt_classes=pt_classes,
                         agents_list=agents_list,
                         order_status='Por Surtir')
    
    df = filter_dataframe_by_range_of_months(
        df,
        date_col='FECHA_ENT',
        base_month=base_month,
        base_year=base_year,
        range_of_months=amount_of_past_months
    )
    
    return df

def get_to_be_supplied_orders_for_trend(base_month: str,
                                        base_year: str,
                                        pt_classes: list[str] = None,
                                        agents_list: list[str] = None,
                                        unit: Literal['MN', 'KG'] = 'MN', 
                                        amount_of_past_months: int = 6) -> float:
    
    df = to_be_supplied_orders_until_base_month(base_month=base_month,
                                                base_year=base_year, 
                                                pt_classes=pt_classes,
                                                agents_list=agents_list,
                                                amount_of_past_months=amount_of_past_months)
    
    if unit == 'KG':
        result = df['SALDO_KG'].sum()
    else:
        result = df['SALDO_PROD_MN'].sum()

    return result


def get_supplied_orders_perecentage(base_month: str,
                                base_year: str,
                                pt_classes: list[str] = None,
                                agents_list: list[str] = None,
                                unit: Literal['MN', 'KG'] = 'MN') -> float:
    
    to_be_supplied = get_to_be_supplied_orders_for_trend(base_month=base_month,
                                            base_year=base_year, 
                                            pt_classes=pt_classes,
                                            agents_list=agents_list,
                                            unit=unit,
                                            amount_of_past_months=1)
    
    total_orders = get_sales_orders_amount(
        base_month=base_month,
        base_year=base_year,
        pt_classes=pt_classes,
        agents_list=agents_list,
        range_of_months=1,
        unit=unit
    )

    return  (1 - (to_be_supplied / total_orders)) if total_orders else 0


def get_so_timeseries(base_month: str,
                      base_year: str,
                      range_of_months: int = 1,
                      pt_classes: list[str] = None,
                      agents_list: list[str] = None,
                      acum: bool = True) -> pd.DataFrame:
    
    df = transform_so_df(base_month=base_month,
                         base_year=base_year,
                         range_of_months=range_of_months,
                         pt_classes=pt_classes,
                         agents_list=agents_list)
    
    df_ts = create_timeline_df(df, 'FECHA_ENT')
    df_ts = df_ts.groupby(df_ts.index)[['TOT_KG', 'SUBT_PROD_MN']].sum()

    if acum:
        df_ts['SUBT_PROD_MN'] = df_ts['SUBT_PROD_MN'].cumsum()
        df_ts['TOT_KG'] = df_ts['TOT_KG'].cumsum()

    return df_ts

def get_sales_orders_by_agent(base_month: str,
                              base_year: str,
                              range_of_months: int = 1,
                              pt_classes: list[str] = None,
                              agents_list: list[str] = None,
                              order_status: Literal['Por Surtir', 'Surtido'] = None,
                              with_business_units: bool = False) -> pd.DataFrame:
    
    df = transform_so_df(
        base_month=base_month,
        base_year=base_year,
        range_of_months=range_of_months,
        pt_classes=pt_classes,
        agents_list=agents_list,
        order_status=order_status
    )

    cols = ['CVE_AGE', 'NOM_AGE']

    if with_business_units:
        cols.append('BU')
        df['BU'] = df['CSE_PROD'].apply(lambda x: get_business_unit(x))

    df = df.groupby(cols)[['SUBT_PROD_MN', 'SALDO_PROD_MN', 'TOT_KG', 'SALDO_KG']].sum()
    df.fillna(0, inplace=True)
    df.reset_index(inplace=True)
    cols.pop(1)
    df.set_index(cols, inplace=True)

    return df


def get_trend_by_agent(base_month: str,
                       base_year: str,
                       range_of_months: int=1,
                       pt_classes: list[str] = None,
                       agents_list: list[str] = None,
                       with_business_units: bool = False) -> pd.DataFrame:
    
    billing = get_net_billing_by_agent(base_month=base_month,
                                                base_year=base_year,
                                                pt_classes=pt_classes,
                                                agents_list=agents_list,
                                                range_of_months=range_of_months,
                                                with_business_units=with_business_units)
    
    orders = get_sales_orders_by_agent(base_month=base_month,
                                        base_year=base_year,
                                        pt_classes=pt_classes,
                                        agents_list=agents_list,
                                        range_of_months=6,
                                        with_business_units=with_business_units)
    
    billing.drop(columns=['NOM_AGE'], inplace=True)
    df = orders.join(billing, how='outer')
    df.fillna(0, inplace=True)

    df['TREND_MN'] = df['NET_MN'] + df['SALDO_PROD_MN']
    df['TREND_KG'] = df['NET_KG'] + df['SALDO_KG']

    df = df[df['TREND_MN'] > 0]

    return df[['NOM_AGE', 'TREND_MN', 'TREND_KG']]


def get_so_and_trend_by_col(so_col_name: str,
                            billing_col_name: str,
                            base_month: str,
                            base_year: str,
                            range_of_months: int = 1,
                            pt_classes: list[str] = None,
                            agents_list: list[str] = None)-> pd.DataFrame:
    """ so_col_name and billing_col_name must contain same values in order to
        perfrom correctly the join between the billing dataframe and the so df"""
    
    to_be_supplied = to_be_supplied_orders_until_base_month(
        base_month=base_month,
        base_year=base_year,
        pt_classes=pt_classes,
        agents_list=agents_list
    )

    billing = get_net_billing_by_col(col_name=billing_col_name,
                                     base_month=base_month,
                                     base_year=base_year, 
                                     pt_classes=pt_classes,
                                     agents_list=agents_list,
                                     range_of_months=range_of_months)

    orders = transform_so_df(
        base_month=base_month,
        base_year=base_year,
        range_of_months=range_of_months,
        pt_classes=pt_classes,
        agents_list=agents_list
    )

    orders = orders.groupby(so_col_name)[['SUBT_PROD_MN', 'TOT_KG']].sum()
    to_be_supplied = to_be_supplied.groupby(so_col_name)[['SALDO_PROD_MN', 'SALDO_KG']].sum()

    df = orders.join(to_be_supplied, how='outer')
    billing.drop(columns=['SUBT_PROD_MN'], inplace=True)
    df = df.join(billing, how='outer')
    df.fillna(0, inplace=True)

    df['TREND_MN'] = df['SALDO_PROD_MN'] + df['NET_MN']
    df['TREND_KG'] = df['SALDO_KG'] + df['NET_KG']

    return df


def get_styled_so_df(base_month: str,
                     base_year: str, 
                     range_of_months=1,
                     all_to_be_supplied_orders: bool = True,
                     pt_classes: list[str] = None,
                     agents_list: list[str] = None):
    
    
    main_df = transform_so_df(
        base_month=base_month,
        base_year=base_year,
        range_of_months=range_of_months,
        pt_classes=pt_classes,
        agents_list=agents_list
    )

    if all_to_be_supplied_orders:
        to_be_supplied_df = to_be_supplied_orders_until_base_month(
            base_month=base_month,
            base_year=base_year,
            pt_classes=pt_classes,
            agents_list=agents_list
        )

        df = pd.concat([to_be_supplied_df, main_df])
        # Index is reseted to drop the sales orders thar are in both dataframes 
        # If two orders are uploaded the same, and index is no reseted, orders may be missing in table
        df = df.reset_index().drop_duplicates()
        df = df.set_index('NO_PED')
        
    else:
        df = main_df

    df['PRECIO_KG_MN'] = df['SUBT_PROD_MN'] / df['TOT_KG']
    cols = ['FECHA_ENT', 'STATUS', 'CSE_PROD', 'CVE_PROD', 'NEW_MED', 'DESC_PROD',
            'CANT_PROD', 'SALDO', 'UNIDAD', 'VALOR_PROD', 'CVE_MON', 'PRECIO_KG_MN', 
            'NOM_AGE', 'NOM_CTE', 'SUBT_PROD_MN', 'TOT_KG', 'FACT_PESO', 'F_ALTA_PED']
    
    df = df[cols]

    status_order = ['Por Surtir', 'Parcial', 'Surtido']
    df['STATUS'] = pd.Categorical(
        df['STATUS'],
        categories=status_order,
        ordered=True
    )

    df = df.sort_values(['STATUS', 'FECHA_ENT'])

    new_name_cols = [
        ('FECHA_ENT', 'Entrega', None),
        ('CSE_PROD', 'Clase', None),
        ('CVE_PROD', 'Clave', None),
        ('NEW_MED', 'Atributo', None),
        ('DESC_PROD', 'Producto', None),
        ('CANT_PROD', 'Ordenado', None),
        ('SALDO', 'Pendiente', None),
        ('VALOR_PROD', 'Precio', to_currency),
        ('CVE_MON', 'Moneda', None),
        ('NOM_AGE', 'Ejecutivo', None),
        ('NOM_CTE', 'Cliente', None),
        ('SUBT_PROD_MN', 'Subtotal (MXN)', to_currency),
        ('TOT_KG', 'Kilogramos', to_kg),
        ('FACT_PESO', 'Factor', None),
        ('F_ALTA_PED', 'Fecha Alta', None),
        ('PRECIO_KG_MN', 'Precio Kg (MXN)', to_currency),
    ]

    for old, new, fmt in new_name_cols: 
        
        if (fmt != None):
            df[old] = df[old].apply(lambda x: fmt(x))

        df.rename(columns={
            old: new
        }, inplace=True)
      
    return df
    
