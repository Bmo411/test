import streamlit as st 
import numpy as np
import matplotlib.pyplot as plt 
import matplotlib.ticker as mtick

from src.config import MONTHS, get_business_unit, get_past_month
from src.utils.formatting import to_currency, to_kg, to_percentage
from src.data.credits import get_credits_df, get_returns_df, get_discounts_df
from src.data.facturas import get_facturas_df
from src.data.clientes import get_clients_df
from src.data.productos import get_products_df

from src.domain.billing_calcs import (get_net_billing, 
                                      get_billing_by_bu_and_cls,
                                      get_net_billing_by_col, 
                                      get_broken_down_billing_data_by_cls, 
                                      transform_credits_df,
                                      transform_billing_df)

def render_sales(month: str, curr_year: str, classes: list = None):

    filtered_month = MONTHS[month]  
    facturas = get_facturas_df()
    clientes = get_clients_df()
    productos = get_products_df()
    ret_and_disc = get_credits_df()

    pastMonth, corrYear = get_past_month(month, curr_year)

    filteredFac = facturas.loc[
        ((facturas['MES'] == filtered_month) &
        (facturas['AÑO'] == curr_year)) | 
        ((facturas['MES'] == MONTHS[pastMonth]) &
        (facturas['AÑO'] == corrYear))
    ].copy()

    filtered_ret_disc = ret_and_disc[(ret_and_disc['MES'] == filtered_month) & (ret_and_disc['AÑO'] == curr_year)]
    discounts_df = get_discounts_df(filtered_ret_disc, facturas)
    returns_df = get_returns_df(filtered_ret_disc, productos)

    if classes:
        filteredFac = filteredFac[filteredFac['CSE_PROD'].isin(classes)]
        discounts_df = discounts_df[discounts_df['CSE_PROD'].isin(classes)]
        returns_df = returns_df[returns_df['CSE_PROD'].isin(classes)]

    filteredFac['FACTURADO'] = np.where(filteredFac['CVE_MON'] == 1, filteredFac['SUBT_PROD'], filteredFac['SUBT_PROD'] * filteredFac['TIP_CAM'])
    maindf = filteredFac.join(clientes, on='CVE_CTE')
    returns_df = returns_df.join(clientes, on='NO_CLIENTE')
    discounts_df = discounts_df.join(clientes, on='NO_CLIENTE')

    
    # DROP CVE_PROD FROM PRODUCTOS TO AVOID DUPLICATED COLUMNS
    productos.drop(['CSE_PROD'], axis=1, inplace=True)
    maindf = maindf.join(productos, on='CVE_PROD')
    # replace null values
    maindf.fillna({'FACT_PESO': 0}, inplace=True) 

    # Assing business unit 
    maindf['UNIDAD_NEGOCIO'] = maindf['CSE_PROD'].apply(lambda x: get_business_unit(x))
    # Get total KG
    maindf['PESO_TOTAL'] = maindf['CANT_SURT'] * maindf['FACT_PESO']

    # Separate last month data from current data
    mask_last_month = (maindf['MES'] == MONTHS[pastMonth]) & (maindf['AÑO'] == corrYear)

    maindf = maindf.loc[~mask_last_month]  

    factByCls = maindf.groupby('CSE_PROD', as_index=False)[['FACTURADO', 'PESO_TOTAL']].sum()
    factByClient = maindf.groupby('NOM_CTE', as_index=False)[['FACTURADO', 'PESO_TOTAL']].sum()

    # Get discounts and returns by class 
    discountsByCls = discounts_df.groupby(['CSE_PROD', 'CSE_DESCUENTO'], as_index=False)[['MONTO_MN']].sum()
    discountsByCls = discountsByCls.pivot(index='CSE_PROD', columns='CSE_DESCUENTO',values='MONTO_MN')
    discountsByCls.reset_index(inplace=True)
    returnsByCls = returns_df.groupby('CSE_PROD', as_index=False)[['PESO_TOTAL_DEV', 'DEVOLUCION_MN']].sum()

    # Add discounts and returns to factByCls 
    factByCls = factByCls.merge(discountsByCls, how='left', on='CSE_PROD')
    factByCls = factByCls.merge(returnsByCls, how='left', on='CSE_PROD')
    factByCls = factByCls.fillna(0)

     # CREATE COLUMNS OF DICOUNTS AND RETURNS IN CASE DOES NOT EXIST 
    for col in ['APLICACION ANTICIPO', 'DESCUENTO', 'PESO_TOTAL_DEV', 'DEVOLUCION_MN']:
        if col not in factByCls.columns:
            factByCls[col] = 0

    # Create dataframe for discounts and returns by class
    negativesByCls = factByCls[['CSE_PROD', 'APLICACION ANTICIPO', 'DESCUENTO', 'DEVOLUCION_MN', 'PESO_TOTAL_DEV']].copy()
    negativesByCls['RESTA_FACT'] = -negativesByCls['APLICACION ANTICIPO'] - negativesByCls['DESCUENTO'] - negativesByCls['DEVOLUCION_MN']
    negativesByCls['RESTA_KG'] = -negativesByCls['PESO_TOTAL_DEV']
    negativesByCls = negativesByCls[['CSE_PROD', 'RESTA_FACT', 'RESTA_KG']]
    negativesByCls['UNIDAD_NEGOCIO'] = negativesByCls['CSE_PROD'].apply(lambda x: get_business_unit(x))

    # Set class as index
    factByCls.set_index('CSE_PROD', inplace=True)

   
    
    factByCls['NETO_FACT'] = factByCls['FACTURADO'] - factByCls['APLICACION ANTICIPO'] - factByCls['DESCUENTO'] - factByCls['DEVOLUCION_MN']
    factByCls['NETO_KG'] = factByCls['PESO_TOTAL'] - factByCls['PESO_TOTAL_DEV']

    for index, column in enumerate(['Facturado MN', 'KG Facturados', 'Anticipos Aplicados', 'Descuentos', 'Devoluciones Kg', 'Devoluciones MN', 'Neto Facturación', 'Neto Kg']):
        cols = ['FACTURADO', 'PESO_TOTAL', 'APLICACION ANTICIPO', 'DESCUENTO', 'PESO_TOTAL_DEV', 'DEVOLUCION_MN', 'NETO_FACT', 'NETO_KG']
        if cols[index] in ['FACTURADO', 'APLICACION ANTICIPO', 'DESCUENTO', 'DEVOLUCION_MN', 'NETO_FACT']:
            pre = "$"
            post = ""
        else: 
            pre = ""
            post = " Kg"
        factByCls[column] = factByCls[cols[index]].apply(lambda x: f"{pre}{x:,.2f}{post}")
        if cols[index] in ['FACTURADO', 'PESO_TOTAL']:
            factByClient[column] = factByClient[cols[index]].apply(lambda x: f"{pre}{x:,.2f}{post}")
    
    factByCls.sort_values(['FACTURADO'], ascending=False, inplace=True)
    factByClient.sort_values(['FACTURADO'], ascending=False, inplace=True)

    monthBilling = maindf['FACTURADO'].sum()
    monthBilling = monthBilling - returns_df['DEVOLUCION_MN'].sum() - discounts_df['MONTO_MN'].sum()

    """Getting distribution of clients"""
    factByClient['FACT_ACUM'] = factByClient['FACTURADO'].apply(lambda x: x / monthBilling).cumsum()
    factByClient['PIE_CLASS'] = factByClient.apply(
        lambda row: row['NOM_CTE'] if row['FACT_ACUM'] < 0.65 else 'OTROS', 
        axis=1
        )
    """
    BILLING IN MXN AND KG BY BUISINESS UNIT BARCHART
    """

    """
    RENDERING ON DATA ON STREAMLIT
    """

    """
    STARTS NEW CALCULATION OF DATA TO RENDER
    """

    billings = {
        'billing_mn': 0,
        'two_months_billing_mn': 0,
        'billing_kg': 0,
        'two_months_billing_kg': 0,
    }

    for range_, unit, key in [
        (1, 'MN', 'billing_mn'),
        (2, 'MN', 'two_months_billing_mn'),
        (1, 'KG', 'billing_kg'),
        (2, 'KG', 'two_months_billing_kg'),
    ]:
        billings[key] = get_net_billing(
            base_month=filtered_month,
            base_year=curr_year,
            range_of_months=range_,
            pt_classes=classes,
            unit=unit,
        )

    last_month_billing_mn = billings['two_months_billing_mn'] - billings['billing_mn']
    last_month_billing_kg = billings['two_months_billing_kg'] - billings['billing_kg']
    delta_mn_percentage = (billings['billing_mn'] - last_month_billing_mn) / last_month_billing_mn
    delta_kg = billings['billing_kg'] - last_month_billing_kg


    # TITLE OF PAGE
    st.header(f"Facturación {month}")

    """
    COLUMNS WITH GENERAL DATA
    """
    col1, col2 = st.columns(2)
    col1.metric("Facturación (MXN)", to_currency(billings['billing_mn']), delta=to_percentage(delta_mn_percentage))
    col2.metric("Facturación (Kg)", to_kg(billings['billing_kg']), delta=to_kg(delta_kg))

    with st.container():
        col1c, col2c = st.columns([3, 1])

        col1c.markdown(
        """
        <div style="padding-top: 18px; font-weight: bold; font-size: 22px;">
            <h4 style="margin: 0; font-weight: bold;">Facturación por unidad de negocio</h4>
        </div>
        """,
        unsafe_allow_html=True
        )
        chart_unit = col2c.selectbox("Facturado", ["MN", "KG"], index=0)

        
        bill_by_bu_and_cls = get_billing_by_bu_and_cls(base_month=filtered_month,
                                                       base_year=curr_year,
                                                       range_of_months=1,
                                                       pt_classes=classes,
                                                       unit=chart_unit)
        
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        bill_by_bu_and_cls.plot(kind="bar", stacked=True, ax=ax1)
        ax1.set_title(f"Facturación por unidad de negocio {chart_unit}")
        ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}' if chart_unit == "MN" else '{x:,.0f} Kg'))
        ax1.legend(
            title='Clase',
            loc='best',
            ncol=3,
            frameon=False
        )

        bar_totals = bill_by_bu_and_cls.sum(axis=1)
        for idx, total in enumerate(bar_totals):
            ax1.text(
                x=idx,
                y=total + total * 0.01,  # un poco arriba de la barra
                s=(f'${total:,.0f}' if chart_unit == "MN" else f'{total:,.0f} Kg'),
                ha='center',
                va='bottom',
                fontsize=9,
                fontweight='bold'
            )
        
        st.pyplot(fig1)

    
    st.dataframe(get_broken_down_billing_data_by_cls(col_name='CSE_PROD',
                                                     base_month=filtered_month,
                                                     base_year=curr_year,
                                                     range_of_months=1,
                                                     pt_classes=classes,
                                                     with_style=True))

    """ Clients pie chart """
    clientsForFig = factByClient.groupby(['PIE_CLASS'], as_index=False)[['FACTURADO']].sum()
    clientsForFig['order'] = clientsForFig['PIE_CLASS'].apply(lambda x: 1 if x == 'OTROS' else 0)
    clientsForFig.sort_values(by=['order', 'FACTURADO'], ascending=[True, False], inplace=True)
    figp, axp = plt.subplots(figsize=(10, 6), facecolor='#ddd')
    axp.pie(clientsForFig['FACTURADO'], labels=clientsForFig['PIE_CLASS'], autopct='%1.1f%%')
    st.divider()
    st.subheader('Facturación por cliente')
    st.pyplot(figp)

    with st.expander("Ver facturación por cliente", icon=":material/contacts_product:"):
        fact_by_client = get_net_billing_by_col(col_name='NOM_CTE',
                                                base_month=filtered_month,
                                                base_year=curr_year,
                                                range_of_months=1,
                                                pt_classes=classes)
        fact_by_client = fact_by_client.sort_values('NET_MN', ascending=False)
        fact_by_client['NET_MN'] = fact_by_client['NET_MN'].apply(lambda x: to_currency(x))
        fact_by_client['NET_KG'] = fact_by_client['NET_KG'].apply(lambda x: to_kg(x))
        st.dataframe(fact_by_client[['NET_MN', 'NET_KG']], width='stretch')


    with st.expander('Facturas del mes', icon=':material/attach_money:'):
        bills_df = transform_billing_df(base_month=filtered_month,
                                        base_year=curr_year, 
                                        pt_classes=classes,
                                        range_of_months=1)

        bills_df.rename(columns={
            'CSE_PROD': 'CLASE',
            'CVE_PROD': 'CLAVE',
            'VALOR_PROD': 'PRECIO_PRODUCTO',
            'CANT_SURT': 'CANTIDAD',
            'FALTA_FAC': 'FECHA',
            'STATUS_FAC': 'STATUS',
            'CVE_MON': 'MONEDA',
            'DESC_PROD': 'DESCRIPCION',
            'FACT_PESO': 'FACTOR',
            'UNI_MED': 'UNIDAD',
            'NOM_CTE': 'CLIENTE',
            'TOT_KG_PROD': 'KILOGRAMOS',
            'SUBT_FAC_MN': 'SUBTOTAL (MXN)'

        }, inplace=True)
        st.dataframe(bills_df[[
            'FECHA', 'STATUS', 'CLIENTE', 'CLASE', 'CLAVE', 'DESCRIPCION', 'CANTIDAD', 'UNIDAD', 'FACTOR',
            'PRECIO_PRODUCTO', 'MONEDA', 'KILOGRAMOS', 'SUBTOTAL (MXN)'
        ]])

    with st.expander('Notas de crédito', icon=':material/money_off:'):
        credits_df = transform_credits_df(
            base_month=filtered_month,
            base_year=curr_year,
            range_of_months=1,
            pt_classes=classes
        )

        credits_df.rename(columns={
            'TIP_NOT': 'NOTA',
            'NO_ESTADO': 'ESTADO',
            'FACT_ID': 'FACTURA',
            'CVE_MON': 'MONEDA',
            'CSE_PROD': 'CLASE',
            'CVE_PROD': 'CLAVE', 
            'VALOR_PROD': 'COSTO',
            'NEWMED': 'ATRIBUTO',
            'TIPO_NOTA': 'TIPO DE NOTA',
            'NOM_CTE': 'CLIENTE',
            'SUBT_MN': 'SUBTOTAL (MXN)',
            'KG_DEVOL': 'DEVOLUCION (KG)'
        }, inplace=True)
        
        st.dataframe(credits_df[[
            'NOTA', 'TIPO DE NOTA', 'FECHA', 'CLIENTE', 'FACTURA', 'ESTADO', 
            'MONEDA', 'SUBTOTAL', 'SALDO', 'CLASE', 'CLAVE', 'ATRIBUTO', 'COSTO',
            'SUBTOTAL (MXN)', 'DEVOLUCION (KG)',
        ]])
        