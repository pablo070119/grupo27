import streamlit as st
import pandas as pd 
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


# Configuración básica de la pagina
st.set_page_config(layout='wide', initial_sidebar_state='expanded')
# Configuración simple para los gráficos
sns.set_style("whitegrid")

# Carga de datos:

@st.cache_data
def cargar_datos():
    # Carga el archivo CSV con datos macrceconómicos
    df = pd.read_csv("data.csv")
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
    return df

df= cargar_datos()

# Barra dashboard

st.sidebar.header('Filtros del Dashboard')

# Extraer nombre y número de mes
df['mes_nombre'] = df['Date'].dt.strftime('%B')
df['mes_num'] = df['Date'].dt.month

# Crear lista de meses con opción "Todos"
meses_unicos = df[['mes_nombre', 'mes_num']].drop_duplicates().sort_values('mes_num')
lista_meses = ["Todos"] + meses_unicos['mes_nombre'].tolist()

# Mostrar selectbox en la barra lateral
mes_seleccionado = st.sidebar.selectbox("Selecciona un mes:", lista_meses)

# Filtrar por mes si no es "Todos"
if mes_seleccionado != "Todos":
    mes_num_seleccionado = meses_unicos[meses_unicos['mes_nombre'] == mes_seleccionado]['mes_num'].values[0]
    df_mes = df[df['Date'].dt.month == mes_num_seleccionado]
else:
    df_mes = df.copy()

# Obtener rango de fechas (filtrado por mes)
min_date = df_mes['Date'].min().to_pydatetime()
max_date = df_mes['Date'].max().to_pydatetime()

# Slider de fechas según ese rango
ini_date, fin_date = st.sidebar.slider(
    "Selecciona un rango de fechas:",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="MM/DD/YYYY"
)

# Filtro final
df_filtrado = df_mes[(df_mes['Date'] >= ini_date) & (df_mes['Date'] <= fin_date)]

# Filtro de línea de productos
lineas_producto = df_filtrado['Product line'].unique()
lineas_seleccionadas = st.sidebar.multiselect(
    "Selecciona las líneas de productos:",
    options=lineas_producto,
    default=lineas_producto  # por defecto seleccionamos todas las líneas
)

# Filtrar por líneas de producto seleccionadas
df_filtrado = df_filtrado[df_filtrado['Product line'].isin(lineas_seleccionadas)]

# título principal dashboard
st.title(' 📊 Dashboard de Ventas')
st.write(f"Datos de ventas de una tienda de conveniencia. ( {ini_date.strftime('%d/%m/%y')} -{fin_date.strftime('%d/%m/%y')})")


st.subheader("Análisis requeridos")

# Opciones de visualización

grafico_opcion = st.radio(
    "Selecciona gráfico a mostrar:",
    ["Ventas Totales por Día",
     "Ingresos por Línea de Producto",
     "Distribución de la Calificación de Clientes",
     "Análisis de Correlación Numérica",
     "Composición del Ingreso Bruto por Sucursal y Línea de Producto"]
)

if grafico_opcion == "Ventas Totales por Día":
    st.subheader("Evolución de las Ventas Totales")
    st.write("*Se muestra cómo han variado las ventas totales a lo largo del tiempo.*")

    # agrupamos ingreso por fecha y agregamos días consecutivos para el gráfico
    df_ventas = df_filtrado.groupby("Date")["Total"].sum().reset_index()
    df_ventas['Día'] = np.arange(1, len(df_ventas) + 1)

    fig, ax = plt.subplots(figsize=(6, 3))
    sns.lineplot(data=df_ventas, x="Día", y="Total", color="#1f77b4", ax=ax)

    ax.set_ylabel("Ventas $")
    ax.set_title("Tendencia de las ventas diarias")
    ax.grid(True, alpha=0.3)

    st.pyplot(fig)

elif grafico_opcion == "Ingresos por Línea de Producto":
    # Agrupar datos por línea de producto
    df_ventas_br = df_filtrado.groupby("Product line")["Total"].sum().reset_index()

    # Crear diccionario de letras
    etiquetas_letras = {nombre: chr(65 + i) for i, nombre in enumerate(df_ventas_br["Product line"])}
    df_ventas_br["Etiqueta"] = df_ventas_br["Product line"].map(etiquetas_letras)

    fig, ax = plt.subplots(figsize=(8, 4))

    # Graficar
    sns.barplot(data=df_ventas_br, x="Etiqueta", y="Total", ax=ax, color="#4c72b0", label="Ingreso Total")

    # Configuración del gráfico
    ax.legend(title="Leyenda")
    ax.set_xlabel("Línea de Producto (codificada)")
    ax.set_ylabel("Total de Ingresos")
    ax.set_title("Ingresos por Línea de Producto")

    st.pyplot(fig)

    # Mostrar tabla de equivalencias (sin nombres de producto, solo letras)
    st.write("**Equivalencias de Línea de Producto:**")
    st.table(pd.DataFrame.from_dict(etiquetas_letras, orient='index', columns=["Letra"]).reset_index().rename(columns={"index": "Product Line"}))

elif grafico_opcion == "Distribución de la Calificación de Clientes":
    st.subheader("Distribución de la Calificación de Clientes")
    st.write("*Este histograma muestra cómo se distribuyen las calificaciones otorgadas por los clientes.*")

    fig, ax = plt.subplots(figsize=(6, 3))

    sns.histplot(
        data=df_filtrado,
        x="Rating",
        bins=10,
        kde=True,
        color="#2ca02c",
        edgecolor="black",
        ax=ax
    )

    ax.set_xlabel("Calificación")
    ax.set_ylabel("Frecuencia")
    ax.set_title("Distribución de Calificaciones de Clientes")
    ax.grid(True, alpha=0.3)

    st.pyplot(fig)

elif grafico_opcion == "Análisis de Correlación Numérica":
    st.subheader("Análisis de Correlación Numérica")
    st.write(
        "*Se utiliza un mapa de calor para visualizar las correlaciones lineales entre variables numéricas. "
        "Como se puede visualizar, es más intuitiva para sacar conclusiones.*"
    )

    variables_numericas = ['Unit price', 'Quantity', 'Tax 5%', 'Total', 'cogs', 'gross income', 'Rating']
    corr_matrix = df_filtrado[variables_numericas].corr(method='pearson')

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", center=0, linewidths=0.5, ax=ax)
    ax.set_title("Matriz de Correlación")

    st.pyplot(fig)


elif grafico_opcion == "Composición del Ingreso Bruto por Sucursal y Línea de Producto":

    st.subheader("Composición del Ingreso Bruto por Sucursal y Línea de Producto")
    st.write(
        "*Se muestra cómo se distribuye el ingreso bruto por línea de producto dentro de cada sucursal. "
        "La altura de cada barra representa el ingreso total por sucursal, y los colores representan las líneas de producto.*"
    )


    df_composicion = df_filtrado.groupby(['Branch', 'Product line'])['gross income'].sum().reset_index()


    df_pivot = df_composicion.pivot(index='Branch', columns='Product line', values='gross income').fillna(0)


    fig, ax = plt.subplots(figsize=(10, 6))
    df_pivot.plot(kind='bar', stacked=True, ax=ax, colormap='tab20')


    ax.set_title("Composición del Ingreso Bruto por Sucursal y Línea de Producto")
    ax.set_xlabel("Sucursal")
    ax.set_ylabel("Ingreso Bruto ($)")
    ax.legend(title="Línea de Producto", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=0)

    st.pyplot(fig)


    df_porcentajes = df_pivot.div(df_pivot.sum(axis=1), axis=0) * 100
    df_porcentajes = df_porcentajes.round(1)  # redondear


    st.write("### Porcentajes de Ingreso Bruto por Línea de Producto dentro de cada Sucursal (%)")
    st.dataframe(df_porcentajes)

