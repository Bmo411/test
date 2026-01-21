import streamlit as st
import numpy as np

from datetime import date, datetime, time

from src.data.clientes import get_clients_df
from src.data.facturas import get_facturas_df
from src.data.agents import get_agents_df

from src.utils.formatting import to_currency
from src.charts.stacked_chart import create_stacked_chart

def aging_class(days : int) -> str:
    if days >= 0: 
        return "No vencido"
    elif days < 0 and days >= -30:
        return "1-30 días"
    elif days < -30 and days >= -60:
        return "31-60 días"
    elif days < -60 and days >= -90:
        return "61-90 días"
    else:
        return "+90 días"
    

def render_portfolio(classes, agents_filter):

    today = date.today()
    bills = get_facturas_df(with_details=False)
    billsD = get_facturas_df()
    clients = get_clients_df()
    agents = get_agents_df(just_name=True)

    # Filter bills with status 'Pagada'
    bills = bills[bills['STATUS_FAC'] != 'Pagada']
    billsD = billsD[billsD['STATUS_FAC'] != 'Pagada']

    bills = bills.join(clients, on='CVE_CTE')
    bills = bills.join(agents, on='CVE_AGE')

    bills['DELTA_DIAS_F_PAGO'] = bills['F_PAGO'].apply(lambda x: (x.date() - today).days)
    bills['BUCKET'] = bills['DELTA_DIAS_F_PAGO'].apply(lambda x: aging_class(x))
    billsInfo = bills[['NOM_CTE', 'DELTA_DIAS_F_PAGO', 'BUCKET', 'NOM_AGE']]

    # Filter clases
    if classes: 
        billsD = billsD[billsD['CSE_PROD'].isin(classes)]
    
    billsD['PERCENTAGE_PRODUCT'] = billsD['SUBT_PROD'] / billsD['SUBT_FAC']
    billsD['SALDO_PROD'] = billsD['SALDO_FAC'] * billsD['PERCENTAGE_PRODUCT']

    billsD = billsD.join(billsInfo)
    
    #Filter Agent 
    if agents_filter:
        bills = bills[bills['NOM_AGE'].isin(agents_filter)]
        billsD = billsD[billsD['NOM_AGE'].isin(agents_filter)]

    billsD['CLIENTE'] = billsD['NOM_CTE'].str.split().str[:2].str.join(" ")
    
    expected_buckets = ["No vencido", "1-30 días", "31-60 días", "61-90 días", "+90 días"]
    
    # Create aging report by client and by sales agent
    pivot_aging = billsD.pivot_table(index=['CVE_CTE','CLIENTE'], columns='BUCKET', values='SALDO_PROD', aggfunc="sum").fillna(0.0)
    pivot_agents = billsD.pivot_table(index=['NOM_AGE'], columns='BUCKET', values='SALDO_PROD', aggfunc='sum').fillna(0.0)

    # Make sure all the columns exists 
    for col in expected_buckets:
        if col not in pivot_aging.columns:
            pivot_aging[col] = 0.0
        if col not in pivot_agents.columns: 
            pivot_agents[col] = 0.0

    # Give correct order to dataframe
    pivot_aging = pivot_aging.abs()
    pivot_aging = pivot_aging[expected_buckets]
    pivot_aging['Total Cliente'] = pivot_aging.sum(axis=1)
    
    expired_df = bills[bills['BUCKET'] != 'No vencido']
    expiredD_df = billsD[billsD['BUCKET'] != 'No vencido']

    # Stacked chart of aging report 
    # Get dataframe of clients with debt 
    stacked_df = pivot_aging.drop(['No vencido', 'Total Cliente'], axis=1)
    stacked_df['Total Cliente'] = stacked_df.sum(axis=1)
    stacked_df.sort_values('Total Cliente', ascending=False, inplace=True)
    if not stacked_df.empty:
        fig1, ax1 = create_stacked_chart(stacked_df.drop('Total Cliente', axis=1).head(30), 
                                        figsize=(12, 8), title='Cartera de clientes con saldo vencido (TOP 30)',
                                        pre_unit='$', with_legend=True, legend_title='Días', bar_label=True, bar_label_rotation=90)

    total_portfolio = billsD['SALDO_PROD'].abs().sum()
    portfolio_expired = expiredD_df['SALDO_PROD'].abs().sum()
    overdue_portfolio_rate = f'{((portfolio_expired / total_portfolio) * 100):,.2f}%'
    clients_with_debt = expiredD_df['CVE_CTE'].nunique()
    avg_days_expired = f'{abs(expired_df['DELTA_DIAS_F_PAGO'].mean()):,.0f}'

    # Edit aging report by agent
    pivot_agents['TOTAL_AGENTE'] = pivot_agents.sum(axis=1)
    pivot_agents.sort_values('TOTAL_AGENTE', ascending=True, inplace=True)
    pivot_agents['Vencido'] = pivot_agents.drop(columns=['No vencido', 'TOTAL_AGENTE']).sum(axis=1)
    pivot_agents = pivot_agents.abs()
    stacked_agents_df = pivot_agents[['No vencido', 'Vencido']]

    # Create stacked chart for agents 
    if not stacked_agents_df.empty:
        fig2, ax2 = create_stacked_chart(stacked_agents_df,
                                         figsize=(10, 4), title='Cartera de clientes por agente',
                                         pre_unit='$', with_legend=True, legend_title='Estado', bar_label=True, bar_label_rotation=90,
                                         with_axes_spines=False)


    """Streamlit dashboard"""
    colt1, colt2 = st.columns([8, 4])
    cold11, cold12 = st.columns(2)
    cold21, cold22, cold23 = st.columns(3)

    colt1.header(f'Cartera de clientes')
    colt2.header(today)
    if not stacked_df.empty:
        cold11.metric("Total por cobrar", to_currency(total_portfolio))
        cold12.metric("Monto vencido", to_currency(portfolio_expired))
        cold21.metric("Tasa de cartera vencida", overdue_portfolio_rate)
        cold22.metric("Clientes con saldo vencido", clients_with_debt)
        cold23.metric('Promedio días vencido', avg_days_expired)

        st.pyplot(fig1)
    else:
        st.subheader('Sin facturas emitidas en sistema, **REVISA FILTROS**')

    st.subheader('Estado de cuentas por cobrar')
    st.dataframe(pivot_aging.sort_values('Total Cliente', ascending=False).style.format(
        lambda x: "" if x == 0 else "${:,.2f}".format(x)
    ))

    if not stacked_agents_df.empty:
        st.subheader('Saldos en cartera por agente', divider=True)
        st.pyplot(fig2)

    with st.expander('Ver saldo de clientes por agente', icon=':material/support_agent:'):
        currDf = (pivot_agents.drop(
            columns=['TOTAL_AGENTE', 'Vencido']
        )[expected_buckets].style.format(
            lambda x: "" if x == 0 else "${:,.2f}".format(x)
        ))
        st.dataframe(currDf)
    
    st.divider()

    with st.expander('Ver detalle de facturas', icon=':material/account_balance_wallet:'):
        # Format billsD dataframe 
        billsD = billsD.rename(columns={
            'CVE_CTE': 'CLAVE CLIENTE',
            'NOM_CTE': 'NOMBRE CLIENTE',
            'NOM_AGE': 'AGENTE',
            'DELTA_DIAS_F_PAGO': 'DIAS VENCIDOS',
            'SALDO_PROD': 'SALDO PRODUCTO',
            'SALDO_FAC': 'SALDO FACTURA',
            'STATUS_FAC': 'STATUS',
            'CVE_PROD': 'CLAVE',
            'CANT_SURT': 'SURTIDO',
            'FALTA_FAC': 'ALTA FACTURA',
            'F_PAGO': 'FECHA PAGO'
        })

        billsD.sort_values(by='FECHA PAGO', inplace=True)


        for col in ['SALDO PRODUCTO', 'SALDO FACTURA']:
            billsD[col] = billsD[col].apply(lambda x: to_currency(x))
        
        for col in ['ALTA FACTURA', 'FECHA PAGO']:
            billsD[col] = billsD[col].dt.strftime("%d/%m/%y")

        st.dataframe(billsD[['CLAVE CLIENTE', 'NOMBRE CLIENTE', 'STATUS', 'CLAVE', 'SURTIDO', 'SALDO PRODUCTO', 'SALDO FACTURA', 'BUCKET', 'DIAS VENCIDOS', 'ALTA FACTURA', 'FECHA PAGO', 'AGENTE']])
