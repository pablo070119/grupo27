import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.express as px

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


st.subheader("Análisis de datos")

# Opciones de visualización

grafico_opcion = st.radio(
    "Selecciona gráfico a mostrar:",
    ["Ventas Totales por Día",
     "Ingresos por Línea de Producto",
     "Distribución de la Calificación de Clientes",
     "Comparación del Gasto por Tipo de Cliente",
     "Relación entre Costo y Ganancia Bruta",
     "Métodos de Pago Preferidos",
     "Análisis de Correlación Numérica",
     "Composición del Ingreso Bruto por Sucursal y Línea de Producto",
     "Relación entre Total Gastado, Cantidad Comprada y Calificación del Cliente (3D)"
     ]
)

if grafico_opcion == "Ventas Totales por Día":
    if lineas_seleccionadas:
        # Aquí agrupamos por fecha
        df_ventas = df_filtrado.groupby('Date')['Total'].sum().reset_index(name='Total de Ventas')

        # Creamos un gráfico de área para mostrar la evolución temporal
        fig, ax = plt.subplots(figsize=(12, 4))

        sns.lineplot(data = df_ventas, x = "Date", y = "Total de Ventas", palette = "viridis", ax = ax)

        # Añadimos barras verticales para distinguir entre semanas
        # Obtenemos las fechas únicas del DataFrame agrupado por día
        fechas_unicas = df_ventas['Date'].unique()

        # Iteramos sobre las fechas y dibujamos una línea vertical para el inicio de cada semana
        for fecha in fechas_unicas:
            # Convertir la fecha a objeto datetime de Python si es necesario (unique() puede devolver numpy.datetime64)
            fecha_dt = pd.to_datetime(fecha)
            # Comprobamos si es el inicio de la semana (lunes)
            if fecha_dt.weekday() == 0: # 0 representa el lunes
                ax.axvline(fecha, color = 'gray', linestyle = "--", alpha = 0.5)

        # Personalizamos el gráfico
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Monto total de ventas diario ($)")
        ax.set_title("Evolución del total de ventas diarias")
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation = 45, ha= 'right')
        st.pyplot(fig)

elif grafico_opcion == "Ingresos por Línea de Producto":
    # Agrupar datos por línea de producto
    df_ventas_br = df_filtrado.groupby("Product line")["Total"].sum().reset_index()

    fig, ax = plt.subplots(figsize=(8, 4))

    # Graficar
    sns.barplot(data=df_ventas_br, x="Product line", y="Total", ax=ax, palette="viridis", dodge="auto")

    # Configuración del gráfico
    ax.set_xlabel("Línea de Producto")
    ax.set_ylabel("Total de Ingresos")
    ax.set_title("Ingresos por Línea de Producto")
    plt.xticks(rotation=45, ha='right')

    st.pyplot(fig)

elif grafico_opcion == "Distribución de la Calificación de Clientes":
    st.subheader("Distribución de la Calificación de Clientes")
    st.write("*Este histograma muestra como se distribuyen las calificaciones otorgadas por los clientes.*")

    fig, ax = plt.subplots(figsize=(6, 3))

    sns.histplot(data=df_filtrado, x="Rating", bins=10, kde=True, palette="viridis",
                 edgecolor="black", ax=ax)

    ax.set_xlabel("Calificación")
    ax.set_ylabel("Frecuencia")
    ax.set_title("Distribución de Calificaciones de Clientes")
    ax.grid(True, alpha=0.3)

    st.pyplot(fig)

elif grafico_opcion == "Comparación del Gasto por Tipo de Cliente":
    st.subheader("Comparación del Gasto por Tipo de Cliente")
    st.write(
        "Se muestra un gráfico circular y un gráfico de barras para indicar la distribución y el total de ventas, respectivamente, según las líneas de producto y el Tipo de Cliente."
    )

    c1_f2, c2_f2 = st.columns(2)

    with c2_f2:
      if lineas_seleccionadas:
          df_linea_producto = df_filtrado.groupby(['Product line', 'Customer type'])['Total'].sum().reset_index(name='Total de Ventas')

          fig, ax = plt.subplots(figsize=(8, 5))

          sns.barplot(data = df_linea_producto, x = "Total de Ventas", y = "Product line",
                      hue = "Customer type", palette = "viridis", ax = ax)

          #Personalizamos el gráfico
          ax.set_xlabel("Línea de Producto", fontsize = 14)
          ax.set_ylabel("Monto total de ventas", fontsize = 14)
          ax.set_title("Total de ventas por línea de producto", fontsize = 18)
          ax.grid(True, alpha=0.3)
          plt.xticks(rotation = 45, ha= 'right')
          plt.tight_layout()
          ax.legend(title="Tipo de cliente", loc="upper right")

          st.pyplot(fig)

      else:
        st.info("Selecciona al menos una categoría de compra para ver el gráfico correctamente")

    with c1_f2:
      if lineas_seleccionadas:
        df_linea_producto = df_filtrado.groupby('Customer type')['Total'].sum().reset_index(name='Total de Ventas')

        Ventas = df_linea_producto['Total de Ventas']
        labels = df_linea_producto['Customer type']

        fig, ax = plt.subplots(figsize=(8, 5))

        ax.pie(
            Ventas,
            labels = labels,
            autopct = '%1.1f%%',
            startangle = 90,
            colors = sns.color_palette('viridis', len(labels))
        )

        ax.axis('equal')

        ax.set_title('Proporción de ventas por tipo de cliente')

        st.pyplot(fig)

elif grafico_opcion == "Relación entre Costo y Ganancia Bruta":
    st.subheader("Relación entre Costo y Ganancia Bruta")
    st.write("Se utiliza un gráfico de dispersión para visualizar la relación entre el costo y la ganancia bruta. Se aprecia una correlación directa.")
    if lineas_seleccionadas:
      fig, ax = plt.subplots(figsize=(8, 5))

      sns.scatterplot(data = df_filtrado, x = "cogs", y = "gross income",
                      palette = "viridis",ax = ax)

      #Personalizamos el gráfico
      ax.set_xlabel("Costo de bienes vendidos", fontsize = 14)
      ax.set_ylabel("Ingreso bruto", fontsize = 14)
      ax.set_title("Relación entre costo de bienes vendidos e ingreso bruto", fontsize = 18)

      st.pyplot(fig)

elif grafico_opcion == "Métodos de Pago Preferidos":
    st.subheader("Métodos de Pago Preferidos")
    st.write("Se muestra un gráfico combinado cuyo eje izquierdo representa la cantidad de compras con cada medio de pago, mientras que el eje derecho representa el monto del total de compras realizadas.")

    if lineas_seleccionadas:
      df_metodo_pago = df_filtrado.groupby('Payment').agg(
          Frecuencia = ('Payment', 'count'),
          Monto_Total = ('Total', 'sum')
      ).reset_index()

      fig, ax1 = plt.subplots(figsize=(8, 5))

      sns.barplot(data = df_metodo_pago, x = "Payment", y = "Frecuencia",
          palette = "viridis", ax = ax1)

      #Personalizamos el primer eje
      ax1.set_xlabel("Método de pago", fontsize = 14)
      ax1.set_ylabel("Frecuencia", fontsize = 14)

      #Creamos el segundo eje y el gráfico
      ax2 = ax1.twinx()

      sns.lineplot(data = df_metodo_pago, x = "Payment", y = "Monto_Total",
                   color = "blue", alpha = 0.6, marker = 'o', ax = ax2)

      #Personalizamos el segundo eje
      ax2.set_ylabel("Monto total de ventas", fontsize = 14)
      ax2.tick_params (axis='y', labelcolor="blue")

      plt.title("Frecuencia y monto total de ventas según método de pago", fontsize = 18)
      plt.tight_layout()

      st.pyplot(fig)
      plt.close(fig)

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

elif grafico_opcion == "Relación entre Total Gastado, Cantidad Comprada y Calificación del Cliente (3D)":
    st.subheader("Relación entre Total Gastado, Cantidad Comprada y Calificación del Cliente")

    if lineas_seleccionadas:
      fig = px.scatter_3d(
          df_filtrado,
          x = "Total",
          y = "Quantity",
          z = "Rating",
          color="Product line",
          hover_data = ["Product line", "Payment"],
          title="Relación entre Total Gastado, Cantidad Comprada y Calificación del Cliente"
      )

      #Personalizamos el gráfico
      fig.update_layout(scene=dict(
          xaxis_title='Total',
          yaxis_title='Quantity',
          zaxis_title='Rating'
          ))

      st.plotly_chart(fig)

# Pie de página simple
st.markdown("---")
st.caption("Dashboard Análisis de Ventas Grupo 27 | Fecha: 21 de mayo 2025")

