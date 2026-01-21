import streamlit as st 

from src.config import MONTHS, MP_CLASSES
from src.utils.formatting import to_currency, to_kg

from src.domain.stock_calcs import get_mp_stocks_with_value_and_avg_cost, render_styled_df
from src.domain.po_calcs import get_prices_by_client_and_resin, get_to_be_supplied_orders_by_resin, get_po_resins_prices_series, get_month_savings, transform_dataframe
from src.charts.normalized_heatmap import create_normalized_heatmap
from src.charts.time_series_chart import create_time_series_chart


def render_purchases(month : str, curr_year: str, business_units: list = None, mp_subclasses: list = None):

    hcol1, hcol2 = st.columns([4, 1])
    hcol1.header(f'Compras {month} {curr_year}', divider=True)
    po_class = hcol2.selectbox('Tipo', MP_CLASSES, index=0)

    month_number=MONTHS[month]
    po_cls_list = [po_class]

    # GET DATA ACCORDING FILTERS
    stock_df = get_mp_stocks_with_value_and_avg_cost(po_classes=po_cls_list, 
                                                     business_units=business_units,
                                                     sub_classes=mp_subclasses)
    
    to_be_supplied_df = get_to_be_supplied_orders_by_resin(base_month=month_number, 
                                                           base_year=curr_year, 
                                                           po_class=po_class, 
                                                           business_units=business_units,
                                                           mp_subclasses=mp_subclasses)

    last_prices = []
    for i in (1, 3, 6):
        temp_df = get_prices_by_client_and_resin(base_month=month_number,
                                                 base_year=curr_year,
                                                 po_class=po_class,
                                                 business_units=business_units, 
                                                 range_of_months=i,
                                                 mp_subclasses=mp_subclasses,
                                                 just_by_resin=True)
        
        if temp_df.empty:
            continue
        
        col_name = f'PROM {i} MESES'
        last_prices.append(col_name)
        temp_df.rename(columns={
            'VALOR_KG_MN': col_name
            }, inplace=True)
        temp_df = temp_df[['SUB_CSE', col_name]]
        stock_df = stock_df.merge(temp_df, how='left', on='SUB_CSE')


    currentStockDF = stock_df[['SUB_CSE', 'EXI_KG', 'VALOR_TOT', 'VALOR_PROM', 'COSTO_MIN_EXI', 'COSTO_MAX_EXI']]
    currentStockDF = currentStockDF.merge(to_be_supplied_df, on='SUB_CSE', how='left')
    
    last_prices.append('SUB_CSE')
    last_prices_df = stock_df[last_prices].copy()
    
    to_be_supplied_df = to_be_supplied_df.merge(last_prices_df, how='outer', on='SUB_CSE')
    to_be_supplied_df.set_index('SUB_CSE', inplace=True)
    to_be_supplied_df = to_be_supplied_df.dropna(how='all')
    to_be_supplied_df.reset_index(inplace=True)

    columns_and_units = (('SUB_CSE', 'RESINA', None),
                            ('EXI_KG', 'EXISTENCIA', 'KG'),
                            ('VALOR_TOT', 'VALOR MN', 'MN'),
                            ('VALOR_PROM', 'COSTO KG', 'KG'),
                            ('COSTO_MIN_EXI', 'COSTO MIN', 'MN'),
                            ('COSTO_MAX_EXI', 'COSTO MAX', 'MN'))
    
    col_and_un_df = (('SUB_CSE', 'RESINA', None),
                         ('SALDO_KG', 'POR RECIBIR', 'KG'),
                         ('TOT_SALDO_MN', 'VALOR', 'MN'),
                         ('COSTO_PROM_OC', 'VALOR KG EN OC', 'MN'))
        

    for currDF, currCols in ((currentStockDF, columns_and_units),
                                (to_be_supplied_df, col_and_un_df)):
        
        if not currDF.empty:
        
            for curr_col, new_col, unit in currCols:
                if unit == 'KG':
                    fmtFun = to_kg
                else:
                    fmtFun = to_currency

                if unit:
                    currDF[curr_col] = currDF[curr_col].apply(lambda x: fmtFun(x))

                currDF.rename(columns={
                    curr_col: new_col
                }, inplace=True)

            currDF.set_index('RESINA', inplace=True)

    last_prices.remove('SUB_CSE')
    for i in last_prices:
        to_be_supplied_df[i] = to_be_supplied_df[i].apply(lambda x: to_currency(x))


    month_savings = get_month_savings(base_month=month_number, 
                                      base_year=curr_year, 
                                      po_class=po_class, 
                                      business_units=business_units, 
                                      mp_subclasses=mp_subclasses)
    
    if month_savings:
        if month_savings > 0:
            mkbadge =  ":green-badge[:material/savings: AHORRO]"
            cap_state = '**:green[ahorro]**'
        else: 
            mkbadge = ":red-badge[:material/credit_card_off: SOBREGASTO]"
            cap_state = '**:red[sobregasto]**'
        
        cap_text = f'''El cambio de precios en {po_class}S en este mes respecto al anterior, 
                  representa un {cap_state} de {to_currency(abs(month_savings))}.'''
    else:
        month_savings = 0
        mkbadge = ":gray-badge[:material/counter_0: SIN ÓRDENES DE COMPRA]"
        cap_text = '''No hay órdenes de compra en este mes o el anterior para calcular 
                        el ahorro por cambios de precios'''


    """
    RENDERING OF DASHBOARD
    """

    mcol1, mcol2 = st.columns([1, 2])
    mcol1.metric('Ahorros por cambios de precios', to_currency(month_savings))
        
    mcol2.markdown(mkbadge)
    mcol2.caption(cap_text)
    
    ts_col1, ts_col2 = st.columns([5, 1])

    ts_col1.subheader(f'Línea de tiempo de precios de {po_class.lower()}s', divider='green')
    ts_range = ts_col2.selectbox('Rango de meses', (int(month_number), 3, 6, 12), index=0)

    ts_data = get_po_resins_prices_series(base_month=month_number, 
                                          base_year=curr_year,
                                          po_class=po_class, 
                                          business_units=business_units, 
                                          mp_subclasses=mp_subclasses,
                                          range_of_months=ts_range)
    
    if not ts_data:
        st.info('Sin información disponible para los filtros seleccionados')
    else:
        figts, axts = create_time_series_chart(time_series=ts_data,
                                                    x_label='Meses',
                                                    y_label='Precio por Kg',
                                                    chart_title='Precios mensuales',
                                                    with_spines='left-bottom',
                                                    all_plots_labels=True,
                                                    y_min=0
                                                    )
    
        st.pyplot(figts)

    st.subheader(f'Existencias y costos de {po_class.lower()}s')

    if currentStockDF.empty:
        st.info('Sin información disponible para filtros seleccionados')

    else:
        st.dataframe(currentStockDF[[
            'EXISTENCIA',
            'VALOR MN',
            'COSTO KG', 
            'COSTO MIN',
            'COSTO MAX',
        ]])
        with st.expander('Ver existencias de materias primas', icon=':material/inventory_2:'):
            st.dataframe(render_styled_df(
                po_classes=po_cls_list,
                stock_of='MP',
                business_units=business_units,
                sub_classes=mp_subclasses
            ))

    if to_be_supplied_df.empty:
        st.info('Sin datos disponibles, revisa filtros seleccioandos')
    else:
        st.dataframe(to_be_supplied_df)
    
    gcol1, gcol2 = st.columns([5, 1])
    gcol1.header(f'Precio de {po_class.lower()}s por proveedor', divider=True)
    
    range = gcol2.selectbox('Ultimos X meses', (1, 3, 6, 12), index=2)

    pivot = get_prices_by_client_and_resin(base_month=month_number, 
                                           base_year=curr_year, 
                                           po_class=po_class, 
                                           business_units=business_units,
                                           mp_subclasses=mp_subclasses,
                                           range_of_months=range)
    if pivot.empty:
        st.info('Sin órdenes de compra para realizar mapa de calor, revisa filtros')
    else: 
        fig, ax = create_normalized_heatmap(pivot, 
                                            title=f'PRECIOS DE {po_class} POR PROVEEDOR', 
                                            x_title='Resinas', 
                                            y_title='Proveedores')
        
        st.pyplot(fig)

    with st.expander('Detalle de órdenes de compra', icon=':material/shopping_cart:'):
        cole1, cole2 = st.columns(2)
        cole1.subheader('Órdenes de compra', divider=True)
        range_months = cole2.select_slider(
            "Meses de órdenes de compra",
            options=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12),
            value=int(month_number),
        )
        st.caption(f'Tabla con las órdenes de compra entregadas en los últimos {range_months} meses')

        pos_df = transform_dataframe(
            base_month=month_number, 
            base_year=curr_year,
            po_class=po_class,
            business_units=business_units,
            mp_subclasses=mp_subclasses,
            range_of_months=range_months
        )
        if pos_df.empty:
            st.info('Sin órdenes de compra')
        else:
            pos_df = pos_df[['CVE_PROD', 'DESC_PROD', 'NEW_MED', 'CANT_PROD', 'SALDO', 'UNI_MED',
                            'VALOR_MN', 'STATUS', 'FECH_ENT', 'NOM_PROV', 'FACT_PESO','F_ALTA_PED']]
            
            pos_df['VALOR_MN'] = pos_df['VALOR_MN'].apply(lambda x: to_currency(x))
            pos_df.sort_values('FECH_ENT', ascending=False, inplace=True)
            pos_df.rename(columns={
                'CVE_PROD': 'CLAVE',
                'DESC_PROD': 'DESCRIPCION',
                'NEW_MED': 'ATRIBUTO',
                'CANT_PROD': 'CANTIDAD ORDENADA',
                'UNI_MED': 'UNIDAD',
                'VALOR_MN': 'PRECIO MXN',
                'FECH_ENT': 'FECHA ENTREGA',
                'NOM_PROV' : 'PROVEEDOR',
                'FACT_PESO': 'FACTOR',
                'F_ALTA_PED': 'ALTA OC',
            }, inplace=True)

            st.dataframe(pos_df)