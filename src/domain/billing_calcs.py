import pandas as pd
import numpy as np

from typing import Literal
from datetime import date

from ..config import get_agents_filtered_list_ids, get_business_unit

from ..data.facturas import get_facturas_df
from ..data.productos import get_products_df
from ..data.credits import get_credits_df
from ..data.agents import get_agents_df
from ..data.clientes import get_clients_df

from ..utils.dates_calculator import filter_dataframe_by_range_of_months
from ..utils.timelines import create_timeline_df
from ..utils.formatting import to_kg, to_currency


"""
FUNCTIONS FOR GETTING DATA ABOUT BILLING 

    FILTER DATAFRAME BY DATES: GIVE THEM A BASE MONTH, BASE YEAR AND A RANGE OF MONTHS TO FILTER THE DATAFRAME 
    TRANSFORM BILLS_DF
    TRANSFORM CREDITS_DF

"""


def _get_bill_cls(fact_id: str, bills_df: pd.DataFrame) -> str:
    if (fact_id == ''):
        return 'OTRO'
    
    bill = bills_df.loc[[fact_id]]
    cls_list = bill['CSE_PROD'].unique()

    if (len(cls_list)) > 1:
        print (f'{fact_id}: Tiene productos de mas de una clase')

    return cls_list[0]

def _get_subtotal_mn_credits_by_product(credit_row) -> float:
    credit_type = credit_row['TIP_NOT']
    if credit_type == 'Dev. Just.':
        value = credit_row['TOT']
    else:
        value = credit_row['SUBTOTAL']

    value_mn = value * np.where(credit_row['CVE_MON'] != 1, credit_row['TIP_CAM'], 1)
    return value_mn


def transform_billing_df(base_month: str, 
                         base_year: str, 
                         pt_classes: list[str], 
                         range_of_months: int,
                         with_details: bool = True,
                         agents_list: list[str] | None = None) -> pd.DataFrame:
    
    # Filter dataframe by date and businees units
    df = get_facturas_df(with_details)
    
    df = filter_dataframe_by_range_of_months(df,
                                             'FALTA_FAC',
                                             base_month,
                                             base_year,
                                             range_of_months)
    
    if with_details:
        if pt_classes: 
            df = df[df['CSE_PROD'].isin(pt_classes)]

        products_df = get_products_df()
        products_df.drop(columns=['CSE_PROD', 'SUB_CSE', 'SUB_SUBCSE'], inplace=True)

        df = df.join(products_df, on='CVE_PROD', how='left')

        df['SUBT_PROD_MN'] = (df['SUBT_PROD'] - df['DESCU_PROD']) * np.where(df['CVE_MON'] != 1, df['TIP_CAM'], 1)
        # TODO: REVISAR SI PREFIEREN QUE COINCIDA CON SAI O NO
        #df['TOT_KG_PROD'] = df['CANT_SURT'] * np.where(df['UNI_MED'] != 'KG', df['FACT_PESO'], 1)
        # TODO HABILITAR CUANDO CUESTIÓNEN PORQUE NO DA IGUAL CON EL SAI
        df['TOT_KG_PROD'] = df['CANT_SURT'] * df['FACT_PESO']

    # Filter agents if agents_list 
    if agents_list and len(agents_list) > 0:
        agents_df = get_agents_df()
        agents_to_filter = get_agents_filtered_list_ids(agents_df, agents_list)
        df = df[df['CVE_AGE'].isin(agents_to_filter)]

    # join clients_df 
    clients = get_clients_df()
    df = df.join(clients, on='CVE_CTE')

    df['SUBT_FAC_MN'] = (df['SUBT_FAC'] - df['DESCUENTO']) * np.where(df['CVE_MON'] != 1, df['TIP_CAM'], 1)

    return df


# credits returns discounts dataframe, and returns dataframe
def transform_credits_df(base_month: str,
                         base_year: str,
                         pt_classes: list[str],
                         range_of_months: int,
                         agents_list: list[str] | None = None) -> pd.DataFrame:
    
    df = get_credits_df()
    df = filter_dataframe_by_range_of_months(
        df,
        'FECHA',
        base_month,
        base_year,
        range_of_months
    )

    if agents_list:
        if len(agents_list) > 0:
            agents_df = get_agents_df()
            agents_to_filter = get_agents_filtered_list_ids(agents_df, agents_list)
            df = df[df['NO_AGENTE'].isin(agents_to_filter)]
    
    # CLASSIFY CREDITS 
    categories = ['ANTI', 'DESC', 'DEVOL']
    conditions = [
        (df['CVE_PROD'] == 'OTRO-40'),
        (df['TIP_NOT'] == 'Descuento'),
        (df['TIP_NOT'] == 'Dev. Just.') & (df['CVE_PROD'] != 'OTRO-40')
    ]

    # Add a type to notes
    df['TIPO_NOTA'] = np.select(conditions, categories, default='SIN_CATEGORIA')

    # Classify credits based on product 
    products = get_products_df()
    products = products[['CSE_PROD', 'FACT_PESO']]

    df = df.join(products, on='CVE_PROD', how='left')

    # Credits to classify based on bill 
    bills_df = get_facturas_df()
    mask = (df['TIPO_NOTA'].isin(['ANTI', 'DESC']))
    df.loc[mask, 'CSE_PROD'] = df.loc[mask]['FACT_ID'].apply(
        lambda row: _get_bill_cls(row, bills_df)
    )

    # Filter classes 
    if pt_classes or len(pt_classes) > 0:
        df = df[df['CSE_PROD'].isin(pt_classes)]

    # Join clients
    clients = get_clients_df()
    df = df.join(clients, on='NO_CLIENTE')

    # GET MN AND KG DATA
    df['SUBT_MN'] = df.apply(lambda x: _get_subtotal_mn_credits_by_product(x), axis=1)
    df['KG_DEVOL'] = np.where(df['TIPO_NOTA'] == 'DEVOL', 
                              df['CANTIDAD'] * np.where(df['UNIDAD'] != 'KG', df['FACT_PESO'], 1), 
                              0)

    return df

# TODO: ADD OPTIONS OF TIME_BLOCKS FOR ANNUAL TIMESERIES
def get_net_billing_timeseries(base_month: str,
                               base_year: str,
                               pt_classes: list[str],
                               agents_list: list[str] = [],
                               range_of_months: int = 1,
                               acum: bool = True,
                               time_blocks: Literal['daily', 'monthly', 'annually'] = 'daily',) -> pd.DataFrame:
    
    bills_df = transform_billing_df(
        base_month=base_month,
        base_year=base_year,
        pt_classes=pt_classes,
        agents_list=agents_list,
        range_of_months=range_of_months
    )

    credits_df = transform_credits_df(
        base_month=base_month,
        base_year=base_year,
        pt_classes=pt_classes,
        agents_list=agents_list,
        range_of_months=range_of_months
    )


    bills_ts = create_timeline_df(bills_df, 'FALTA_FAC')
    credits_ts = create_timeline_df(credits_df, 'FECHA')

    bills_ts = bills_ts.groupby(bills_ts.index)[['SUBT_PROD_MN', 'TOT_KG_PROD']].sum()
    credits_ts = credits_ts.groupby(credits_ts.index)[['SUBT_MN', 'KG_DEVOL']].sum()

    ts = bills_ts.join(credits_ts)
    ts = ts.fillna(0)

    ts['NET_MN'] = ts['SUBT_PROD_MN'] - ts['SUBT_MN']
    ts['NET_KG'] = ts['TOT_KG_PROD'] - ts['KG_DEVOL']
    if acum:
        ts['NET_MN'] = ts['NET_MN'].cumsum()
        ts['NET_KG'] = ts['NET_KG'].cumsum()

    ts = ts[['NET_MN', 'NET_KG']]

    return ts

def get_net_billing_by_agent(base_month: str,
                             base_year: str,
                             pt_classes: str = None,
                             agents_list: str = None,
                             range_of_months: int = 1,
                             with_business_units: bool = False) -> pd.DataFrame:
    
    bills_df = transform_billing_df(
        base_month=base_month,
        base_year=base_year,
        pt_classes=pt_classes,
        agents_list=agents_list,
        range_of_months=range_of_months
    )

    credits_df = transform_credits_df(
        base_month=base_month,
        base_year=base_year,
        pt_classes=pt_classes,
        agents_list=agents_list,
        range_of_months=range_of_months
    )

    cols_bills = ['CVE_AGE']
    cols_credits = ['NO_AGENTE']
    if with_business_units:
        bills_df['BU'] = bills_df['CSE_PROD'].apply(lambda x: get_business_unit(x))
        credits_df['BU'] = credits_df['CSE_PROD'].apply(lambda x: get_business_unit(x))

        cols_bills.append('BU')
        cols_credits.append('BU')

    bills_df = bills_df.groupby(cols_bills)[['SUBT_PROD_MN', 'TOT_KG_PROD']].sum()
    credits_df = credits_df.groupby(cols_credits)[['SUBT_MN', 'KG_DEVOL']].sum()

    agents_df = get_agents_df(just_name=True)

    # Rename credits columns for the join 
    credits_df.index.names = ['CVE_AGE', 'BU'] if with_business_units else ['CVE_AGE']

    agents_billing_df = bills_df.join(credits_df)
    agents_billing_df.fillna(0, inplace=True)
    agents_billing_df = agents_billing_df.join(agents_df, on='CVE_AGE')

    agents_billing_df['NET_MN'] = agents_billing_df['SUBT_PROD_MN'] - agents_billing_df['SUBT_MN']
    agents_billing_df['NET_KG'] = agents_billing_df['TOT_KG_PROD'] - agents_billing_df['KG_DEVOL']
    agents_billing_df['AVG_PRICE_KG'] = agents_billing_df['SUBT_PROD_MN'] / agents_billing_df['TOT_KG_PROD']

    return agents_billing_df[['NOM_AGE', 'NET_MN', 'NET_KG', 'AVG_PRICE_KG']]


def get_net_billing_by_col(col_name: str,
                            base_month: str,
                            base_year: str,
                            pt_classes: str = None,
                            agents_list: str = None,
                            range_of_months: int = 1) -> pd.DataFrame:
    
    bills_df = transform_billing_df(
        base_month=base_month,
        base_year=base_year,
        pt_classes=pt_classes,
        agents_list=agents_list,
        range_of_months=range_of_months
    )

    credits_df = transform_credits_df(
        base_month=base_month,
        base_year=base_year,
        pt_classes=pt_classes,
        agents_list=agents_list,
        range_of_months=range_of_months
    )

    bills_df = bills_df.groupby(col_name)[['SUBT_PROD_MN', 'TOT_KG_PROD']].sum()
    credits_df = credits_df.groupby(col_name)[['SUBT_MN', 'KG_DEVOL']].sum()

    df = bills_df.join(credits_df)
    df.fillna(0, inplace=True)

    df['NET_MN'] = df['SUBT_PROD_MN'] - df['SUBT_MN']
    df['NET_KG'] = df['TOT_KG_PROD'] - df['KG_DEVOL']
    df['AVG_PRICE_KG'] = df['SUBT_PROD_MN'] / df['TOT_KG_PROD']

    #return df[['NET_MN', 'NET_KG', 'AVG_PRICE_KG']]
    return df


"""
FUNCTION FOR CALCULATING DATA
"""

def get_net_billing(base_month: str,
                    base_year: str,
                    range_of_months: str = 1,
                    pt_classes: list[str] = None,
                    agents_list: list[str] = None,
                    unit: Literal['MN','KG'] = 'MN') -> float:
    
    bills = transform_billing_df(base_month=base_month,
                                 base_year=base_year,
                                 range_of_months=range_of_months,
                                 pt_classes=pt_classes,
                                 agents_list=agents_list)
    
    credits = transform_credits_df(base_month=base_month,
                                   base_year=base_year,
                                   range_of_months=range_of_months,
                                   pt_classes=pt_classes,
                                   agents_list=agents_list)
    
    if unit == 'KG':
        cols = ('TOT_KG_PROD', 'KG_DEVOL')
    else:
        cols = ('SUBT_PROD_MN', 'SUBT_MN')

    billing = bills[cols[0]].sum()
    credit = credits[cols[1]].sum()

    net_billing = billing - credit
    return net_billing


def get_day_billing(date: date,
                    pt_classes: list[str] = None,
                    agents_list: list[str] = None,
                    unit: Literal['MN', 'KG'] = 'MN') -> float:
    
    month = date.month 
    year = date.year 

    bills = transform_billing_df(
        base_month=month,
        base_year=year, 
        range_of_months=1,
        pt_classes=pt_classes,
        agents_list=agents_list
    )

    credits = transform_credits_df(
        base_month=month,
        base_year=year,
        range_of_months=1,
        pt_classes=pt_classes,
        agents_list=agents_list
        )

    bills = bills[bills['FALTA_FAC'].dt.date == date]
    credits = credits[credits['FECHA'].dt.date == date]

    if unit == 'KG':
        cols = ('TOT_KG_PROD', 'KG_DEVOL')
    else:
        cols = ('SUBT_PROD_MN', 'SUBT_MN')

    net_day_billing = bills[cols[0]].sum() - credits[cols[1]].sum()

    return net_day_billing


def get_billing_by_bu_and_cls(base_month: str,
                              base_year: str,
                              range_of_months: int,
                              pt_classes: list[str] = None,
                              agent_list: list[str] = None,
                              unit: Literal['MN', 'KG'] = 'MN') -> pd.DataFrame:
    
    billings_df = transform_billing_df(base_month=base_month,
                                        base_year=base_year,
                                        range_of_months=range_of_months,
                                        pt_classes=pt_classes,
                                        agents_list=agent_list)
    
    credits_df = transform_credits_df(base_month=base_month,
                                        base_year=base_year,
                                        range_of_months=range_of_months,
                                        pt_classes=pt_classes,
                                        agents_list=agent_list)
    
    if unit == 'KG':
        col_names = {
            'bill': 'TOT_KG_PROD',
            'credit': 'KG_DEVOL',
        }
    else:
        col_names = {
            'bill': 'SUBT_PROD_MN',
            'credit': 'SUBT_MN'
        }
    
    billings_df['UNIDAD_NEGOCIO'] = billings_df['CSE_PROD'].apply(lambda x: get_business_unit(x))
    credits_df['UNIDAD_NEGOCIO'] = credits_df['CSE_PROD'].apply(lambda x: get_business_unit(x))

    billings_pivot = billings_df.pivot_table(index='UNIDAD_NEGOCIO', columns='CSE_PROD', values=col_names['bill'], aggfunc='sum').fillna(0)
    credits_pivot = credits_df.pivot_table(index='UNIDAD_NEGOCIO', columns='CSE_PROD', values=col_names['credit'], aggfunc='sum').fillna(0)

    pivot = billings_pivot.sub(credits_pivot, fill_value=0)
    return pivot

def get_broken_down_billing_data_by_cls(col_name: str,
                                        base_month: str,
                                        base_year: str,
                                        range_of_months: int = 1,
                                        pt_classes: list[str] = None,
                                        agents_list: list[str] = None,
                                        with_style: bool = False) -> pd.DataFrame:
    

    df = get_net_billing_by_col(col_name=col_name,
                                base_month=base_month,
                                base_year=base_year,
                                range_of_months=range_of_months,
                                pt_classes=pt_classes,
                                agents_list=agents_list)

    credits_df = transform_credits_df(base_month=base_month,
                                      base_year=base_year,
                                      range_of_months=range_of_months,
                                      pt_classes=pt_classes,
                                      agents_list=agents_list)
    
    credits_df = credits_df[credits_df['TIPO_NOTA'] == 'ANTI']

    credits_df = credits_df.groupby(col_name)[['SUBT_MN']].sum()
    credits_df.rename(columns={
        'SUBT_MN': 'ANTI_APLICA'
    }, inplace=True)

    df = df.join(credits_df, how='outer')

    df.fillna(0, inplace=True)
    df['DEV_DESC_MN'] = df['SUBT_MN'] - df['ANTI_APLICA']

    df = df.replace(0, np.nan).dropna(how='all')
    df.fillna(0, inplace=True)

    if with_style:

        new_cols = [
            ('NET_MN', 'MN', 'Facturación neta (MXN)'),
            ('NET_KG', 'KG', 'Facturación neta (KG)'),
            ('SUBT_PROD_MN', 'MN', 'Facturado (MXN)'),
            ('TOT_KG_PROD', 'KG', 'Facturado (KG)'),
            ('AVG_PRICE_KG', 'MN', 'Precio Kg (MXN)'),
            ('ANTI_APLICA', 'MN', 'Anticipos Aplicados (MXN)'),
            ('DEV_DESC_MN', 'MN', 'Devoluciones y Descuentos (MXN)'),
            ('KG_DEVOL', 'KG', 'Devoluciones (KG)'),
        ]

        for old_col, curr_unit, new_col in new_cols:

            if curr_unit == 'KG':
                to_format = to_kg
            else: 
                to_format = to_currency

            df[old_col] = df[old_col].apply(lambda x: to_format(x))
            df.rename(columns={old_col:new_col}, inplace=True)

        return df[[
            'Facturación neta (MXN)',
            'Facturación neta (KG)',
            'Facturado (MXN)',
            'Facturado (KG)',
            'Precio Kg (MXN)',
            'Anticipos Aplicados (MXN)',
            'Devoluciones y Descuentos (MXN)',
            'Devoluciones (KG)',
        ]] 
    
    return df

