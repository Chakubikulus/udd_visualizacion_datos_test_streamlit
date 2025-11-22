"""
Aplicación Streamlit para Visualización de Emisiones de CO₂
Convierte el análisis del notebook en una aplicación web interactiva
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import os

# Configuración de la página
st.set_page_config(
    page_title="Emisiones de CO₂ Global",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("🌍 Visualización de Emisiones de CO₂ por País")
st.markdown("---")

# ============================================
# FUNCIÓN PARA CARGAR DATOS (con caché)
# ============================================
@st.cache_data
def load_data():
    """Carga los datos de shapefile y CSV con caché para mejor rendimiento"""
    # Obtener el directorio del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Rutas a los archivos de datos
    shp_path = os.path.join(script_dir, 'data', 'ne_50m_admin_0_countries', 'ne_50m_admin_0_countries.shp')
    csv_path = os.path.join(script_dir, 'data', 'annual-co2-emissions-per-country.csv')
    
    # Cargar shapefile
    world = gpd.read_file(shp_path)
    world = world.rename(columns={'ISO_A3': 'code'})
    world['code'] = world['code'].str.upper()
    
    # Cargar emisiones
    df = pd.read_csv(csv_path)
    df = df.rename(columns={'Entity': 'country', 'Code': 'code', 'Year': 'year'})
    df['code'] = df['code'].str.upper()
    
    # Filtrar a códigos ISO válidos
    df = df[df['code'].str.len() == 3]
    
    # Quedarnos con la columna de emisiones
    value_col = [c for c in df.columns if c not in ['country', 'code', 'year']]
    df = df.rename(columns={value_col[0]: 'co2'})
    
    # Crear maestro de países
    world_master = (
        world[['code', 'NAME', 'geometry']]
        .drop_duplicates(subset=['code'])
        .rename(columns={'NAME': 'country'})
        .set_index('code')
    )
    
    return df, world_master

# Cargar datos
try:
    df, world_master = load_data()
    countries = sorted(df['country'].unique())
    years = sorted(df['year'].unique())
except FileNotFoundError as e:
    st.error(f"❌ Error: No se encontraron los archivos de datos. Asegúrate de que los archivos estén en la carpeta 'data'.")
    st.stop()
except Exception as e:
    st.error(f"❌ Error al cargar los datos: {str(e)}")
    st.stop()

# ============================================
# SIDEBAR CON INFORMACIÓN Y CONTROLES
# ============================================
with st.sidebar:
    st.header("📊 Información")
    st.info(f"**Países disponibles:** {len(countries)}")
    st.info(f"**Rango de años:** {years[0]} - {years[-1]}")
    st.info(f"**Total de registros:** {len(df):,}")
    
    st.markdown("---")
    st.markdown("### 🎯 Navegación")
    st.markdown("Usa las pestañas arriba para explorar diferentes visualizaciones")

# ============================================
# TABS PARA DIFERENTES VISUALIZACIONES
# ============================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Serie Temporal", 
    "🏆 Ranking por Año", 
    "📊 Emisiones Acumuladas",
    "🌐 Tendencia Global",
    "🗺️ Mapa Animado"
])

# ============================================
# TAB 1: SERIE TEMPORAL POR PAÍS
# ============================================
with tab1:
    st.header("📈 Emisiones de CO₂ a lo largo del tiempo")
    st.markdown("Selecciona un país para ver su evolución de emisiones de CO₂")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        selected_country = st.selectbox(
            "Selecciona un país:",
            options=countries,
            index=countries.index('Chile') if 'Chile' in countries else 0
        )
    
    with col2:
        st.empty()
    
    # Filtrar datos
    subset = df[df['country'] == selected_country].sort_values('year')
    subset = subset.dropna(subset=['co2'])
    
    if len(subset) > 0:
        # Mostrar métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Emisiones 2021", f"{subset[subset['year']==subset['year'].max()]['co2'].values[0]:,.0f} ton")
        with col2:
            st.metric("Emisiones 1990", f"{subset[subset['year']==subset['year'].min()]['co2'].values[0]:,.0f} ton")
        with col3:
            st.metric("Años de datos", len(subset))
        with col4:
            st.metric("Emisiones máximas", f"{subset['co2'].max():,.0f} ton")
        
        # Gráfico
        fig = px.line(
            subset,
            x='year',
            y='co2',
            title=f'Emisiones de CO₂ a lo largo del tiempo — {selected_country}',
            labels={'co2': 'CO₂ (toneladas)', 'year': 'Año'},
            line_shape='linear'
        )
        fig.update_layout(template='simple_white', height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"No hay datos disponibles para {selected_country}")

# ============================================
# TAB 2: RANKING POR AÑO
# ============================================
with tab2:
    st.header("🏆 Top 15 Países por Emisiones de CO₂")
    st.markdown("Selecciona un año para ver el ranking de países")
    
    selected_year = st.slider(
        "Selecciona un año:",
        min_value=int(years[0]),
        max_value=int(years[-1]),
        value=int(years[-1]),
        step=1
    )
    
    # Filtrar y ordenar datos
    df_year = df[df['year'] == selected_year].dropna(subset=['co2'])
    df_year = df_year.sort_values('co2', ascending=False).head(15)
    
    if len(df_year) > 0:
        # Mostrar tabla
        st.dataframe(
            df_year[['country', 'co2']].rename(columns={'country': 'País', 'co2': 'Emisiones (toneladas)'}),
            use_container_width=True,
            hide_index=True
        )
        
        # Gráfico de barras
        fig = px.bar(
            df_year,
            x='co2',
            y='country',
            orientation='h',
            title=f"Top 15 países por emisiones de CO₂ en {selected_year}",
            labels={
                'co2': 'CO₂ (toneladas)',
                'country': 'País'
            }
        )
        fig.update_layout(
            template='simple_white',
            yaxis={'categoryorder': 'total ascending'},
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"No hay datos disponibles para el año {selected_year}")

# ============================================
# TAB 3: EMISIONES ACUMULADAS
# ============================================
with tab3:
    st.header("📊 Emisiones Acumuladas de CO₂")
    st.markdown("Visualiza las emisiones acumuladas a lo largo del tiempo para un país")
    
    selected_country_cum = st.selectbox(
        "Selecciona un país:",
        options=countries,
        index=countries.index('United States') if 'United States' in countries else 0,
        key="country_cumulative"
    )
    
    # Calcular emisiones acumuladas
    subset_cum = df[df['country'] == selected_country_cum].sort_values('year')
    subset_cum = subset_cum.dropna(subset=['co2'])
    subset_cum['cumulative'] = subset_cum['co2'].cumsum()
    
    if len(subset_cum) > 0:
        # Mostrar métricas
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Emisiones totales acumuladas", f"{subset_cum['cumulative'].max():,.0f} ton")
        with col2:
            st.metric("Emisiones promedio anual", f"{subset_cum['co2'].mean():,.0f} ton")
        
        # Gráfico
        fig = px.area(
            subset_cum,
            x='year',
            y='cumulative',
            title=f"Emisiones acumuladas de CO₂ — {selected_country_cum}",
            labels={
                'cumulative': 'CO₂ acumulado (toneladas)',
                'year': 'Año'
            }
        )
        fig.update_layout(template='simple_white', height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"No hay datos disponibles para {selected_country_cum}")

# ============================================
# TAB 4: TENDENCIA GLOBAL + TOP 10
# ============================================
with tab4:
    st.header("🌐 Tendencia Global y Top 10 Países")
    st.markdown("Compara la tendencia global con los 10 países con mayores emisiones acumuladas")
    
    # Calcular tendencia global
    global_trend = (
        df.groupby('year', as_index=False)['co2']
          .sum()
          .rename(columns={'co2': 'co2_global'})
    )
    global_trend['country'] = 'World'
    global_trend = global_trend.rename(columns={'co2_global': 'co2'})
    
    # Top 10 países por emisiones acumuladas
    country_totals = (
        df.groupby('country', as_index=False)['co2']
          .sum()
          .sort_values('co2', ascending=False)
    )
    top10_countries = country_totals.head(10)['country'].tolist()
    
    df_top10 = df[df['country'].isin(top10_countries)].copy()
    
    # Unir top10 + tendencia global
    df_global_top10 = pd.concat([df_top10, global_trend], ignore_index=True)
    
    # Mostrar top 10
    st.subheader("Top 10 países por emisiones acumuladas (todo el período)")
    st.dataframe(
        country_totals.head(10)[['country', 'co2']].rename(
            columns={'country': 'País', 'co2': 'Emisiones Totales (toneladas)'}
        ),
        use_container_width=True,
        hide_index=True
    )
    
    # Gráfico
    fig = px.line(
        df_global_top10.sort_values(['country', 'year']),
        x='year',
        y='co2',
        color='country',
        title='Tendencia global de emisiones de CO₂ y top 10 países por emisiones acumuladas',
        labels={
            'year': 'Año',
            'co2': 'CO₂ (toneladas)',
            'country': 'País'
        }
    )
    fig.update_layout(template='simple_white', height=600)
    st.plotly_chart(fig, use_container_width=True)

# ============================================
# TAB 5: MAPA ANIMADO
# ============================================
with tab5:
    st.header("🗺️ Mapa Animado de Emisiones de CO₂")
    st.markdown("Explora la evolución de las emisiones de CO₂ en el mapa mundial")
    
    # Preparar datos para el mapa
    df_map = df[df['code'].str.len() == 3].copy()
    df_map = df_map.dropna(subset=['co2'])
    df_map = df_map.sort_values(by='year')
    
    # Crear mapa animado
    fig_map_anim = px.choropleth(
        df_map,
        locations='code',
        color='co2',
        hover_name='country',
        animation_frame='year',
        color_continuous_scale='Reds',
        projection='natural earth',
        title='Mapa animado de emisiones anuales de CO₂',
        labels={'co2': 'CO₂ (toneladas)'}
    )
    
    fig_map_anim.update_layout(
        geo=dict(showcountries=True, showcoastlines=True),
        height=700
    )
    
    # Ajustar velocidad de animación
    if len(fig_map_anim.layout.updatemenus) > 0:
        fig_map_anim.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 100
        fig_map_anim.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 0
    
    st.plotly_chart(fig_map_anim, use_container_width=True)
    
    st.info("💡 Usa los controles de reproducción en el mapa para animar la visualización")

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <p>Visualización de Emisiones de CO₂ | Datos de Our World in Data</p>
    </div>
    """,
    unsafe_allow_html=True
)

