import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from src.config import MONTHS, get_business_unit
from src.data.resultados_prod import get_res_ops_df
from src.data.productos import get_products_df
from src.utils.formatting import to_currency, to_kg


def render_production(month: str, curr_year: str, classes: list):
    
    # Get filtered data 
    filtered_month = MONTHS[month]
    results = get_res_ops_df()

    # Filter results of current month and year
    res_df = results.loc[
        (results['FECH_ORDP'].dt.month == int(filtered_month)) &
        (results['FECH_ORDP'].dt.year == int(curr_year))
    ].copy()

    # Join products to df
    products = get_products_df()
    res_df = res_df.join(products, on='CVE_COPR')

    # REPLACE VALUES WITH NO FACT_PESO
    res_df.fillna({'FACT_PESO': 0}, inplace=True)

    #Assign business unit
    res_df['UNIDAD_NEGOCIO'] = res_df['CSE_PROD'].apply(lambda x: get_business_unit(x))
    
    # Filter classes
    if classes:
        res_df = res_df[res_df['CSE_PROD'].isin(classes)]

    # Get kg produced 
    res_df['KILOGRAMOS_PRODUCIDOS'] = res_df['REN_COPR'] * res_df['FACT_PESO']
    res_df['COSTO_TOTAL'] = res_df['REN_COPR'] * res_df['CTO_UNIT']
    res_df['COSTO_POR_KG'] = res_df['COSTO_TOTAL'] / res_df['KILOGRAMOS_PRODUCIDOS']

    # GET AVERGAE COST OF KG BY CLASS
    resCls = res_df.groupby(['UNIDAD_NEGOCIO', 'CSE_PROD'], as_index=False)[['KILOGRAMOS_PRODUCIDOS', 'COSTO_TOTAL']].sum()
    resCls['COSTO_PROMEDIO_KG'] = resCls['COSTO_TOTAL'] / resCls['KILOGRAMOS_PRODUCIDOS']
    resCls['Costo promedio por Kg'] = resCls['COSTO_PROMEDIO_KG'].apply(lambda x: to_currency(x))
    resCls['Kilogramos producidos'] = resCls['KILOGRAMOS_PRODUCIDOS'].apply(lambda x: to_kg(x))
    resCls['Valor producido'] = resCls['COSTO_TOTAL'].apply(lambda x: to_currency(x))
    resCls.sort_values(['COSTO_PROMEDIO_KG'], ascending=True, inplace=True)

    # Get total kg produced 
    total_kg = res_df['KILOGRAMOS_PRODUCIDOS'].sum()
    total_cost = res_df['COSTO_TOTAL'].sum()
    
    # Create bar chart for average cost
    figProm, axProm = plt.subplots(figsize=(10, 6))
    paletteProm = sns.color_palette("colorblind", n_colors=len(resCls))
    sns.barplot(data=resCls, x='CSE_PROD', y='COSTO_PROMEDIO_KG', hue='CSE_PROD', ax=axProm, palette=paletteProm, legend=False)
    axProm.set_title('Costo promedio por kg por clase', fontsize=16)
    axProm.set_xlabel('Clase', fontsize=12)
    axProm.set_ylabel('MXN ($)', fontsize=12)

    for container in axProm.containers:
        axProm.bar_label(container, fmt='$%.2f', label_type='edge', fontsize=10, padding=3)


    # Format results dataframe for displaying
    res_df = res_df.rename(columns={
        "NO_ORDP": "Resultado",
        "CVE_COPR": "Clave",
        'REN_COPR': 'Producido',
        'CTO_UNIT': 'Costo unitario',
        'NO_OPRO': 'Orden', 
        'DATOEST4': 'Línea',
        'NEW_COPR': 'Atributo', 
        'UNI_MED': 'Unidad',
        'DESC_PROD': 'Producto',
        'FECH_ORDP': 'Fecha',
        'FACT_PESO': 'Factor',
        'COSTO_POR_KG' : 'Costo Kg',
        'KILOGRAMOS_PRODUCIDOS':  'Kilos totales',
    })
    res_df['Fecha'] = res_df['Fecha'].dt.date
    res_df.sort_values(by=['Orden', 'Resultado'], ascending=[True, True], inplace=True)


    # Streamlit dashboard
    st.header(f'Producción {month}')
    col1t, col2t = st.columns(2)
    col1t.metric('Valor producido', f'${total_cost:,.2f}')
    col2t.metric('Kilogramos producidos', f'{total_kg:,.2f} kg')
    st.subheader('Costo de productos')
    st.pyplot(figProm)
    st.dataframe(resCls[['CSE_PROD', 'Costo promedio por Kg', 'Kilogramos producidos', 'Valor producido']].reset_index(drop=True), use_container_width=True)
    st.divider()

    with st.container():
        col1Prod, col2Prod = st.columns([3,1])
        col1Prod.markdown(
        """
        <div style="padding-top: 18px; font-weight: bold; font-size: 22px;">
            <h4 style="margin: 0; font-weight: bold;">Producción por unidad de negocio</h4>
        </div>
        """,
        unsafe_allow_html=True
        )
        productionChart = col2Prod.selectbox("Visualizar por", ["KG", "Monto"], index=0)

        # Create chart based on selection
        # Create bar chart for production by business unit
        if productionChart == "KG":
            pivotedDFCls = resCls.pivot_table(index='UNIDAD_NEGOCIO', columns='CSE_PROD', values='KILOGRAMOS_PRODUCIDOS', aggfunc="sum").fillna(0)
            productionTitle = 'Kilogramos producidos por unidad de negocio'
        else: 
            pivotedDFCls = resCls.pivot_table(index='UNIDAD_NEGOCIO', columns='CSE_PROD', values='COSTO_TOTAL', aggfunc="sum").fillna(0)
            productionTitle = 'Valor producido por unidad de negocio'

        paletteProd = sns.color_palette("Paired", n_colors=len(pivotedDFCls.columns))

        figProd, axProd = plt.subplots(figsize=(10, 8))
        pivotedDFCls.plot(kind="bar", stacked=True, ax=axProd, color=paletteProd)

        axProd.set_title(productionTitle)
        axProd.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f} Kg' if productionChart == "KG" else '${x:,.0f}'))
        axProd.set_xlabel("Unidad de negocio", fontsize=12)
        axProd.legend(
            title='Clase',
            loc='best',
            ncol=3,
        )
        total_bars = pivotedDFCls.sum(axis=1)
        for idx, total in enumerate(total_bars):
            axProd.text(
                x=idx,
                y= total + total * 0.01,
                s=(f'{total:,.0f} Kg' if productionChart == "KG" else f'${total:,.0f}'),
                ha='center',
                va='bottom',
                fontsize=10
            )
        st.pyplot(figProd)
    
    with st.expander("Ver resultados de producción", icon=":material/factory:"):
        st.dataframe(res_df[['Orden', 'Resultado', 'Clave', 'Atributo', 'Producto', 'Producido', 'Unidad', 'Costo unitario', 'Costo Kg', 'Factor', 'Kilos totales', 'Línea', 'Fecha']].reset_index(drop=True), use_container_width=True)