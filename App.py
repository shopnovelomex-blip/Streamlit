%%writefile app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

st.set_page_config(page_title="Análisis de Ventas y Ganancias", layout="wide")

# Ruta del archivo
file_path = 'SalidaVentas.xlsx'

@st.cache_data
def load_data():
    df = pd.read_excel(file_path)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"No se pudo cargar el archivo: {e}")
    st.stop()

st.title("📈 Dashboard de Análisis de Ventas y Rendimiento")
st.markdown("Este dashboard replica de manera interactiva todo el análisis exploratorio realizado sobre el archivo de ventas, con especial foco en identificar las causas de pérdidas financieras.")

# Sidebar para filtros generales
st.sidebar.header("Filtros Generales")
regiones_disponibles = ["Todas"] + list(df['Region'].unique())
region_seleccionada = st.sidebar.selectbox("Selecciona Región", regiones_disponibles)

if region_seleccionada != "Todas":
    df_filtrado = df[df['Region'] == region_seleccionada]
else:
    df_filtrado = df

# KPIs Generales
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Ventas Totales", f"${df_filtrado['Sales'].sum():,.2f}")
with col2:
    st.metric("Ganancias Totales", f"${df_filtrado['Profit'].sum():,.2f}", delta=f"{df_filtrado['Profit'].sum():,.2f}")
with col3:
    st.metric("Cantidad de Productos", f"{int(df_filtrado['Quantity'].sum()):,}")
with col4:
    st.metric("Descuento Promedio", f"{df_filtrado['Discount'].mean():.1%}")

# Pestañas de Análisis
tab1, tab2, tab3 = st.tabs(["📊 Distribución y Correlación", "🌍 Análisis Regional", "🔍 Caso de Pérdidas (West)"])

with tab1:
    st.header("Distribuciones Generales de Ventas y Ganancias")
    col_t1_1, col_t1_2 = st.columns(2)
    
    with col_t1_1:
        limite_sales = df['Sales'].quantile(0.95)
        df_filtrado_sales = df[df['Sales'] <= limite_sales]
        fig, ax = plt.subplots()
        sns.histplot(data=df_filtrado_sales, x='Sales', kde=True, ax=ax, color='royalblue')
        ax.set_title(f'Distribución de Sales (Hasta percentil 95: ${limite_sales:.2f})')
        st.pyplot(fig)
        
    with col_t1_2:
        limite_inf_profit = df['Profit'].quantile(0.025)
        limite_sup_profit = df['Profit'].quantile(0.975)
        df_filtrado_profit = df[(df['Profit'] >= limite_inf_profit) & (df['Profit'] <= limite_sup_profit)]
        fig, ax = plt.subplots()
        sns.histplot(data=df_filtrado_profit, x='Profit', kde=True, ax=ax, color='forestgreen')
        ax.set_title(f'Distribución de Profit (Rango central 95%)')
        st.pyplot(fig)

    st.subheader("Relación entre Ventas y Ganancias (Correlación)")
    correlacion = df['Sales'].corr(df['Profit'])
    st.write(f"El coeficiente de correlación de Pearson entre Sales y Profit es: **{correlacion:.4f}**")
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.regplot(data=df, x='Sales', y='Profit', scatter_kws={'alpha':0.3, 'color':'royalblue'}, line_kws={'color':'red'}, ax=ax)
    st.pyplot(fig)

with tab2:
    st.header("Desempeño Regional")
    col_t2_1, col_t2_2 = st.columns(2)
    
    with col_t2_1:
        st.subheader("Distribución de Ventas por Región")
        ventas_por_region = df.groupby('Region')['Sales'].sum().reset_index()
        fig, ax = plt.subplots()
        ax.pie(ventas_por_region['Sales'], labels=ventas_por_region['Region'], autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
        st.pyplot(fig)
        
    with col_t2_2:
        st.subheader("Distribución de Ganancias por Región")
        ganancias_por_region = df.groupby('Region')['Profit'].sum().reset_index()
        fig, ax = plt.subplots()
        ax.pie(ganancias_por_region['Profit'], labels=ganancias_por_region['Region'], autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
        st.pyplot(fig)

    st.subheader("Detalle de Estados dentro de la Región Seleccionada")
    if region_seleccionada == "Todas":
        st.info("Por favor, selecciona una región específica en la barra lateral para ver el desglose por estado.")
    else:
        ganancias_estado = df_filtrado.groupby('State')['Profit'].sum().reset_index().sort_values(by='Profit', ascending=False)
        fig, ax = plt.subplots(figsize=(12, 5))
        sns.barplot(data=ganancias_estado, x='State', y='Profit', palette='viridis', ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)
        st.dataframe(ganancias_estado.style.format({'Profit': '${:,.2f}'}))

with tab3:
    st.header("Análisis del Problema: Pérdidas en la Región West")
    st.markdown("Investigamos los tres estados de la región West que reportaron pérdidas significativas: **Colorado, Arizona y Oregon**.")
    
    df_west = df[df['Region'] == 'West']
    estados_con_perdidas = ['Colorado', 'Arizona', 'Oregon']
    df_perdidas = df_west[df_west['State'].isin(estados_con_perdidas)]
    
    # Tabla resumen de métricas
    resumen_estados = df_perdidas.groupby('State').agg(
        Ventas_Totales=('Sales', 'sum'),
        Ganancias_Totales=('Profit', 'sum'),
        Descuento_Promedio=('Discount', 'mean'),
        Total_Transacciones=('Discount', 'count')
    ).reset_index()
    st.subheader("Resumen de Pérdidas")
    st.dataframe(resumen_estados.style.format({
        'Ventas_Totales': '${:,.2f}',
        'Ganancias_Totales': '${:,.2f}',
        'Descuento_Promedio': '{:.1%}'
    }))
    
    # Niveles de descuento y su impacto
    st.subheader("Impacto de los Niveles de Descuento en la Ganancia Promedio")
    ganancias_por_descuento = df_perdidas.groupby(['State', 'Discount'])['Profit'].mean().reset_index()
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=ganancias_por_descuento, x='Discount', y='Profit', hue='State', ax=ax)
    ax.set_xticklabels([f"{x*100:.0f}%" for x in ganancias_por_descuento['Discount'].unique()])
    ax.set_ylabel("Ganancia Promedio ($)")
    st.pyplot(fig)
    
    # Productos culpables
    st.subheader("Top Sub-Categorías con mayores pérdidas acumuladas")
    perdidas_subcat = df_perdidas.groupby(['State', 'Category', 'Sub-Category']).agg(
        Ventas_Totales=('Sales', 'sum'),
        Ganancias_Totales=('Profit', 'sum'),
        Descuento_Promedio=('Discount', 'mean')
    ).reset_index().sort_values(by='Ganancias_Totales', ascending=True).head(10)
    st.dataframe(perdidas_subcat.style.format({
        'Ventas_Totales': '${:,.2f}',
        'Ganancias_Totales': '${:,.2f}',
        'Descuento_Promedio': '{:.1%}'
    }))
