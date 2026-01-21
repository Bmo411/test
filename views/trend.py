import streamlit as st

from datetime import datetime, timedelta

from src.config import MONTHS, UNITS

from src.utils.formatting import to_currency, to_kg, to_percentage

from src.charts.time_series_chart import create_time_series_chart
from src.charts.stacked_horizontal_chart import create_stacked_horizontal_chart

from src.domain.so_calcs import (get_styled_so_df,
                                 get_sales_orders_amount,
                                 get_to_be_supplied_orders_for_trend,
                                 get_supplied_orders_perecentage,
                                 get_trend_by_agent,
                                 get_so_and_trend_by_col,
                                 get_so_timeseries,
                                 to_be_supplied_orders_until_base_month)

from src.domain.billing_calcs import (get_net_billing, 
                                      get_net_billing_timeseries, 
                                      get_net_billing_by_agent,
                                      get_day_billing)

# Mostrar la siguiente información por clase 
"""
ESTADISTICAS A MOSTRAR:
    proyeccion de facturacion 
    

INFORMACION DE TABLA:
    Pedidos a surtir en mes seleccionado (monto y kg) (basarte en fecha de entrega)
    Facturado por clase de SAI
    Mostrar precio objetivo por clase y unidad de negocio y cumpliminete de este 
    Mostrar pedidos pendientes por surtir
"""

def render_trend(month: str, curr_year: str, classes: list = None, agents_filter = list):
    
    filtered_month = MONTHS[month]

    """BASE DAY COULD BE YESTERDAY O LAST DAY OF MONTH"""
    today = datetime.now()
    next_month = int(filtered_month) + 1
    if next_month > 12:
        next_month -= 12

    last_day_month = datetime(year=int(curr_year), month=next_month, day=1) - timedelta(days=1)
    if today > last_day_month:
        base_day = last_day_month
    else:
        base_day = today

    month_advance = base_day.day / last_day_month.day

    so_month_mn = get_sales_orders_amount(
        base_month=filtered_month,
        base_year=curr_year,
        pt_classes=classes,
        agents_list=agents_filter,
        range_of_months=1,
        unit='MN'
    )

    so_month_kg = get_sales_orders_amount(
        base_month=filtered_month,
        base_year=curr_year,
        pt_classes=classes,
        agents_list=agents_filter,
        range_of_months=1,
        unit='KG'
    )

    # Get timeseries of billing 
    billing_ts = get_net_billing_timeseries(base_month=filtered_month,
                                            base_year=curr_year,
                                            pt_classes=classes,
                                            agents_list=agents_filter,
                                            acum=True,
                                            range_of_months=1)
    
    so_ts = get_so_timeseries(base_month=filtered_month,
                              base_year=curr_year,
                              range_of_months=1,
                              pt_classes=classes,
                              agents_list=agents_filter,
                              acum=True)
    

    trend_by_agent_with_bu = get_trend_by_agent(base_month=filtered_month,
                                    base_year=curr_year,
                                    range_of_months=1,
                                    pt_classes=classes,
                                    agents_list=agents_filter,
                                    with_business_units=True)

    billing_by_agent_with_bu = get_net_billing_by_agent(
        base_month=filtered_month,
        base_year=curr_year,
        pt_classes=classes,
        agents_list=agents_filter,
        range_of_months=1,
        with_business_units=True
    )

        

    # RENDERING OF INFORMATION
    st.title(f'Trend de ventas {month}')

    if agents_filter:
        if len(agents_filter) == 1:
            names = agents_filter[0]
        else: 
            names = ", ".join(agents_filter[:-1]) + " y " + agents_filter[-1]

        st.caption(f'Trend de ventas de {names}')

    # Trend metrics 
    col1, col2, col3 = st.columns([4, 4, 2])
    col1.metric("Pedidos MN", to_currency(so_month_mn))
    col2.metric('Pedidos en KG', to_kg(so_month_kg))

    with st.expander('Tendencia de ventas', expanded=True, icon=':material/trending_up:'):
        etcol1, etcol2 = st.columns([3, 1])

        etcol1.subheader('Estadísticas de ventas', divider=True)
        stats_unit = etcol2.selectbox('Unidad', UNITS)

        if so_month_mn < 1: 
            st.info(f"""Si el filtro está en un mes dónde no hay pedidos, la tendencia que se muestra son todos los
                        pedidos que están "Por Surtir" y "Parcial" hasta el último día del mes de {month}""")

        day_billing = get_day_billing(base_day.date(),
                                  pt_classes=classes,
                                  agents_list=agents_filter,
                                  unit=stats_unit)
        
        past_day_billing = get_day_billing((base_day - timedelta(days=1)).date(),
                                            pt_classes=classes,
                                            agents_list=agents_filter,
                                            unit=stats_unit)
        
        # If the past day does not have billing, returns 0
        diff_day_billing = (day_billing - past_day_billing) / past_day_billing if past_day_billing > 0 else 0


        billing = get_net_billing(
            base_month=filtered_month,
            base_year=curr_year,
            range_of_months=1,
            pt_classes=classes,
            agents_list=agents_filter,
            unit=stats_unit
        )

        two_months_billing = get_net_billing(
            base_month=filtered_month,
            base_year=curr_year,
            range_of_months=2,
            pt_classes=classes,
            agents_list=agents_filter,
            unit=stats_unit
        )

        to_be_supplied = get_to_be_supplied_orders_for_trend(
            base_month=filtered_month,
            base_year=curr_year,
            pt_classes=classes,
            agents_list=agents_filter,
            unit=stats_unit
        )

        past_month_billing = two_months_billing - billing

        sales_trend = billing + to_be_supplied

        delta_trend = (sales_trend - past_month_billing) / past_month_billing if past_month_billing > 0 else 0
        delta_billing = (billing - past_month_billing) / past_month_billing if past_month_billing > 0 else 0


        daily_billing = get_net_billing_timeseries(base_month=filtered_month,
                                        base_year=curr_year,
                                        pt_classes=classes,
                                        agents_list=agents_filter,
                                        acum=False)
        
        supplied_percentage2 = get_supplied_orders_perecentage(
            base_month=filtered_month,
            base_year=curr_year,
            pt_classes=classes,
            agents_list=agents_filter,
            unit=stats_unit
        )
        
        if stats_unit == 'KG':
            metric_ts = daily_billing['NET_KG']
            to_format = to_kg
        else:
            metric_ts = daily_billing['NET_MN']
            to_format = to_currency

        ecol1, ecol2, ecol3 = st.columns(3)

        ecol1.metric(f'Facturado el {base_day.strftime("%d/%m/%y")}', to_format(day_billing), delta=to_percentage(diff_day_billing), chart_data=metric_ts, chart_type='line')
        ecol2.metric('Trend de ventas', to_format(sales_trend), delta=to_percentage(delta_trend))
        ecol2.metric('Por surtir', to_format(to_be_supplied))

        ecol3.metric('Facturación', to_format(billing), delta=to_percentage(delta_billing))
        ecol31, ecol32 = ecol3.columns(2)
        ecol31.metric('Surtido', to_percentage(supplied_percentage2, with_decimals=False))
        ecol32.metric('Avance del mes', to_percentage(month_advance, with_decimals=False))

        st.caption('*Comparaciones sobre facturación del mes pasado')


    # trend chart container
    with st.container():
        col21, col22 = st.columns([3, 1])
        col21.header('Pedidos vs Facturación', divider=True)
        chart_data = col22.selectbox('Unidades', ['MN', 'KG'], index=0, key=22)

        if chart_data == 'MN':
            curr_data = [
                (so_ts['SUBT_PROD_MN'], 'Pedidos'),
                (billing_ts['NET_MN'], 'Facturación MN'),
            ]
        else: 
            curr_data = [
                (so_ts['TOT_KG'], 'Trend de Kg'),
                (billing_ts['NET_KG'], 'Kg facturados'),
            ]
        if curr_data[0][0].empty and curr_data[1][0].empty:
            st.info('Sin información disponible para filtro seleccionado')
        else:
            fig, ax = create_time_series_chart(curr_data,
                                            'Fecha', 
                                            'Monto MN', 
                                            'Pedidos Colocados VS Facturación', 
                                            figsize=(12, 8), 
                                            unit=chart_data)

            st.pyplot(fig)

    so_and_trend_by_cls = get_so_and_trend_by_col(so_col_name='CSE_PROD',
                                                  billing_col_name='CSE_PROD',
                                                  base_month=filtered_month,
                                                  base_year=curr_year,
                                                  range_of_months=1,
                                                  pt_classes=classes,
                                                  agents_list=agents_filter)
    # Improve style of df 
    so_and_trend_by_cls['AVG_P_T'] = so_and_trend_by_cls['TREND_MN'] / so_and_trend_by_cls['TREND_KG']
    trend_by_cls_cols = [
        ('SUBT_PROD_MN', 'MN', 'Pedidos MXN'),
        ('TOT_KG', 'KG', 'Pedidos Kg'),
        ('SALDO_PROD_MN', 'MN', 'Por surtir MXN'),
        ('SALDO_KG', 'KG', 'Por surtir Kg'),
        ('NET_MN', 'MN', 'Facturación MXN'),
        ('NET_KG', 'KG', 'Facturación Kg'),
        ('TREND_MN', 'MN', 'Trend MXN'),
        ('TREND_KG', 'KG', 'Trend Kg'),
        ('AVG_P_T', 'MN', 'Precio Kg trend'),
        ('AVG_PRICE_KG', 'MN', 'Precio Kg facturación')
    ]

    for col_data in trend_by_cls_cols:
        if col_data[1] == 'KG':
            to_format = to_kg
        else:
            to_format = to_currency
            
        so_and_trend_by_cls[col_data[0]] = so_and_trend_by_cls[col_data[0]].apply(lambda x: to_format(x))

        so_and_trend_by_cls.rename(columns={
            col_data[0]: col_data[2]
        }, inplace=True)

    

    st.dataframe(so_and_trend_by_cls[[
        'Trend MXN',
        'Trend Kg',
        'Facturación MXN',
        'Facturación Kg',
        'Por surtir MXN',
        'Por surtir Kg',
        'Precio Kg facturación',
        'Precio Kg trend',
        'Pedidos MXN',
        'Pedidos Kg',
    ]])
    
    
    # Trend by sales man container 
    with st.container():
        col31, col32, col33 = st.columns([3, 1, 1])
        col31.header('Venta por Agente')

        if trend_by_agent_with_bu.empty:
            st.info('Sin información disponible para los filtros seleccionados')
        else:
            agentsDataChart = col32.selectbox('Datos', ['Trend', 'Facturación'], index=0, key=32)
            agentsChartUnits = col33.selectbox('Unidades', ['MN', 'KG'], index=0, key=33)

            if agentsDataChart == 'Trend':
                pivot_data = trend_by_agent_with_bu
                columns_dict = {
                    'MN': 'TREND_MN',
                    'KG': 'TREND_KG',
                }
                graph_title = 'Trend por agente'
            else: 
                pivot_data = billing_by_agent_with_bu
                columns_dict = {
                    'MN': 'NET_MN',
                    'KG': 'NET_KG',
                }
                graph_title = 'Facturación por agente'

            xlabel_title = {
                'MN': 'Monto en MN',
                'KG': 'Kilogramos',
            }

            format_fun = {
                'MN': to_currency,
                'KG': to_kg
            }
            
            agents_pivot_table = pivot_data.pivot_table(index='NOM_AGE', columns='BU', values=columns_dict[agentsChartUnits], aggfunc='sum', fill_value=0)

            # Sort agents by interest value
            agents_pivot_table['TTEMP'] = agents_pivot_table.sum(axis=1)
            agents_pivot_table.sort_values('TTEMP', ascending=True, inplace=True)
            agents_df_to_render = agents_pivot_table.sort_values('TTEMP', ascending=False)
            agents_pivot_table.drop(columns='TTEMP', inplace=True) 
            agents_df_to_render.drop(columns=['TTEMP'], inplace=True)
            
            fig2, ax2 = create_stacked_horizontal_chart(agents_pivot_table,
                                                        xlabel_title[agentsChartUnits],
                                                        'Agentes',
                                                        figsize=(16,9),
                                                        units=agentsChartUnits,
                                                        legend='Unidades de negocio',
                                                        with_bar_notations=True,
                                                        title=graph_title)

            st.pyplot(fig2)
            if agents_df_to_render.empty:
                st.info('Sin información disponible, revisa filtros')
            else:
                st.subheader(f'**{graph_title} ({agentsChartUnits})**')
                st.dataframe(agents_df_to_render.style.format(
                    lambda x: "" if x == 0 else format_fun[agentsChartUnits](x)
                ))
    
    with st.expander('Pedidos del mes actual y por surtir', icon=':material/shopping_cart:'):
        st.dataframe(get_styled_so_df(base_month=filtered_month,
                                    base_year=curr_year,
                                    range_of_months=1,
                                    pt_classes=classes,
                                    agents_list=agents_filter))

    
    