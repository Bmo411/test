import streamlit as st
from datetime import datetime 

from src.config import MONTHS, BUSINESS_UNITS, PAGES, MP_SUBCLASSES,get_agents_dict, YEAR_OPTIONS, YEAR_INDEX
from src.data.agents import get_agents_df


from views.sales import render_sales
from views.production import render_production
from views.client_portfolio import render_portfolio
from views.trend import render_trend
from views.purchases import render_purchases


def main():

    # Get agents from database 
    agents = get_agents_df()
    agents_dict = get_agents_dict(agents)

    with st.sidebar:
        st.title("LAMINEX Dashboards")
        st.markdown("## GRAFICOS")
        page = st.selectbox("Página", PAGES, index=0)

        st.divider()
        st.markdown("## Filtros")

        if page != 'Cartera':
            month = st.selectbox("Seleción de mes", list(MONTHS.keys()), index=((datetime.now().month) - 1))

        if page in ['Trend de ventas', 'Cartera'] :
            agents = st.multiselect("Equipo de ventas",
                                options=agents_dict.keys())

        business_units = st.multiselect("Unidad de negocio", options=BUSINESS_UNITS.keys())

        selected_classes = []
        for unit in business_units:
            selected_classes.extend(BUSINESS_UNITS[unit])
            
        if page == 'Compras':
            mp_subclasses = st.multiselect('Materia Prima', 
                                           options=MP_SUBCLASSES,
                                           default=[])
        else:
            classes = st.multiselect("Clases SAI", 
                                    options=[cls for group in BUSINESS_UNITS.values() for cls in group],
                                    default=selected_classes)
            
        if page != 'Cartera':
            selected_year = st.selectbox('Selección de Año', YEAR_OPTIONS, index=YEAR_INDEX)
        

    if page == "Facturación":
        render_sales(month, selected_year, classes)
    elif page == "Producción":
        render_production(month, selected_year, classes)
    elif page == 'Cartera':
        render_portfolio(classes, agents)
    elif page == 'Trend de ventas':
        render_trend(month, selected_year, classes, agents)
    elif page == 'Compras':
        render_purchases(month, selected_year, business_units, mp_subclasses)




main()


