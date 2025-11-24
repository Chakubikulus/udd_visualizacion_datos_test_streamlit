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
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("Visualización de Emisiones de CO₂ por País")
st.markdown("""
**Análisis interactivo de emisiones de CO₂ a nivel global**  
Esta aplicación permite explorar las emisiones de dióxido de carbono por país desde 1750 hasta la actualidad, 
proporcionando múltiples perspectivas para entender las tendencias y patrones globales.
""")
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
    st.error(f"Error: No se encontraron los archivos de datos. Asegúrate de que los archivos estén en la carpeta 'data'.")
    st.stop()
except Exception as e:
    st.error(f"Error al cargar los datos: {str(e)}")
    st.stop()

# ============================================
# SIDEBAR CON INFORMACIÓN Y CONTROLES
# ============================================
with st.sidebar:
    st.header("Información del Dataset")
    st.info(f"**Países disponibles:** {len(countries)}")
    st.info(f"**Rango de años:** {years[0]} - {years[-1]}")
    st.info(f"**Total de registros:** {len(df):,}")
    
    st.markdown("---")
    st.markdown("### Sobre los Datos")
    st.caption("""
    **Fuente:** Our World in Data - Global Carbon Budget  
    **Unidad:** Toneladas de CO₂  
    **Alcance:** Emisiones territoriales (dentro de fronteras)  
    **Nota:** No incluye emisiones de aviación/shipping internacional
    """)
    
    st.markdown("---")
    st.markdown("### Navegación")
    st.markdown("Usa las pestañas arriba para explorar diferentes visualizaciones")
    
    st.markdown("---")
    st.markdown("### Búsqueda Rápida")
    search_country = st.selectbox(
        "Buscar país:",
        options=[""] + countries,
        index=0
    )
    if search_country:
        st.info(f"País seleccionado: **{search_country}**")

# ============================================
# TABS PARA DIFERENTES VISUALIZACIONES
# ============================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Serie Temporal", 
    "Ranking por Año", 
    "Emisiones Acumuladas",
    "Tendencia Global",
    "Mapa Animado"
])

# ============================================
# TAB 1: SERIE TEMPORAL POR PAÍS
# ============================================
with tab1:
    st.header("Serie Temporal de Emisiones de CO₂")
    st.markdown("""
    **Visualización:** Línea temporal  
    **Marca:** Línea continua  
    **Canal visual:** Posición en eje Y (magnitud), posición en eje X (tiempo)  
    **Justificación:** La línea temporal permite identificar tendencias, quiebres y patrones de crecimiento/declive. 
    La posición vertical codifica la magnitud de emisiones, facilitando la comparación de valores entre años.
    """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        selected_country = st.selectbox(
            "Selecciona un país:",
            options=countries,
            index=countries.index('Chile') if 'Chile' in countries else 0
        )
        
        # Opción de comparar con otro país
        compare_enabled = st.checkbox("Comparar con otro país", value=False)
        if compare_enabled:
            compare_country = st.selectbox(
                "País a comparar:",
                options=[c for c in countries if c != selected_country],
                index=0
            )
    
    with col2:
        st.empty()
    
    # Filtrar datos
    subset = df[df['country'] == selected_country].sort_values('year')
    subset = subset.dropna(subset=['co2'])
    
    if compare_enabled:
        subset_compare = df[df['country'] == compare_country].sort_values('year')
        subset_compare = subset_compare.dropna(subset=['co2'])
    
    if len(subset) > 0:
        # Calcular estadísticas adicionales
        latest_year = subset['year'].max()
        latest_value = subset[subset['year']==latest_year]['co2'].values[0]
        first_year = subset['year'].min()
        first_value = subset[subset['year']==first_year]['co2'].values[0]
        max_year = subset.loc[subset['co2'].idxmax(), 'year']
        max_value = subset['co2'].max()
        
        # Calcular tasa de crecimiento promedio
        if len(subset) > 1:
            growth_rate = ((latest_value / first_value) ** (1/(latest_year - first_year)) - 1) * 100
        else:
            growth_rate = 0
        
        # Mostrar métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                f"Emisiones {int(latest_year)}", 
                f"{latest_value:,.0f} ton",
                delta=f"{((latest_value - first_value) / first_value * 100):.1f}% vs {int(first_year)}" if first_value > 0 else None
            )
        with col2:
            st.metric(f"Emisiones {int(first_year)}", f"{first_value:,.0f} ton")
        with col3:
            st.metric("Años de datos", len(subset))
        with col4:
            st.metric(
                f"Emisiones máximas ({int(max_year)})", 
                f"{max_value:,.0f} ton"
            )
        
        # Gráfico
        if compare_enabled and len(subset_compare) > 0:
            fig = px.line(
                pd.concat([
                    subset.assign(comparison='Principal'),
                    subset_compare.assign(comparison='Comparación')
                ]),
                x='year',
                y='co2',
                color='comparison',
                title=f'Comparación de Emisiones de CO₂: {selected_country} vs {compare_country}',
                labels={'co2': 'CO₂ (toneladas)', 'year': 'Año', 'comparison': 'País'},
                line_shape='linear'
            )
            fig.update_traces(line=dict(width=3))
        else:
            fig = px.line(
                subset,
                x='year',
                y='co2',
                title=f'Emisiones de CO₂ a lo largo del tiempo — {selected_country}',
                labels={'co2': 'CO₂ (toneladas)', 'year': 'Año'},
                line_shape='linear'
            )
            fig.update_traces(line=dict(width=3, color='#1f77b4'))
        
        fig.update_layout(
            template='plotly_white',
            height=500,
            hovermode='x unified',
            xaxis_title="Año",
            yaxis_title="Emisiones de CO₂ (toneladas)"
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        st.plotly_chart(fig, use_container_width=True)
        
        # Análisis interpretativo
        with st.expander("Análisis e Interpretación", expanded=False):
            st.markdown(f"""
            **Observaciones para {selected_country}:**
            - **Período de datos:** {int(first_year)} - {int(latest_year)} ({len(subset)} años)
            - **Emisiones actuales:** {latest_value:,.0f} toneladas de CO₂
            - **Emisiones históricas iniciales:** {first_value:,.0f} toneladas de CO₂
            - **Pico de emisiones:** {max_value:,.0f} toneladas en {int(max_year)}
            - **Tasa de crecimiento promedio anual:** {growth_rate:.2f}%
            
            **Interpretación:** {'Las emisiones han aumentado significativamente' if growth_rate > 0 else 'Las emisiones han disminuido' if growth_rate < 0 else 'Las emisiones se han mantenido estables'} 
            desde {int(first_year)} hasta {int(latest_year)}. {'El pico de emisiones ocurrió en ' + str(int(max_year)) + ', ' + ('antes' if max_year < latest_year else 'recientemente') + ' del período analizado.' if max_year != latest_year else 'Las emisiones más altas corresponden al año más reciente.'}
            """)
    else:
        st.warning(f"No hay datos disponibles para {selected_country}")

# ============================================
# TAB 2: RANKING POR AÑO
# ============================================
with tab2:
    st.header("Ranking de Países por Emisiones de CO₂")
    st.markdown("""
    **Visualización:** Gráfico de barras horizontales  
    **Marca:** Barras rectangulares  
    **Canal visual:** Longitud de barra (magnitud), posición vertical (ranking)  
    **Justificación:** Las barras horizontales facilitan la lectura de nombres de países y la comparación de magnitudes. 
    La longitud codifica la cantidad de emisiones, permitiendo identificar rápidamente los mayores emisores.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_year = st.slider(
            "Selecciona un año:",
            min_value=int(years[0]),
            max_value=int(years[-1]),
            value=int(years[-1]),
            step=1
        )
    
    with col2:
        top_n = st.selectbox(
            "Top N países:",
            options=[10, 15, 20, 25, 30],
            index=1
        )
    
    # Filtrar y ordenar datos
    df_year = df[df['year'] == selected_year].dropna(subset=['co2'])
    df_year = df_year.sort_values('co2', ascending=False).head(top_n)
    
    if len(df_year) > 0:
        # Calcular estadísticas
        total_top_n = df_year['co2'].sum()
        total_global = df[df['year'] == selected_year]['co2'].sum()
        percentage = (total_top_n / total_global * 100) if total_global > 0 else 0
        
        # Mostrar métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Top N", f"{total_top_n:,.0f} ton")
        with col2:
            st.metric("Total Global", f"{total_global:,.0f} ton")
        with col3:
            st.metric("Porcentaje del total", f"{percentage:.1f}%")
        
        # Mostrar tabla
        st.subheader(f"Tabla: Top {top_n} países en {selected_year}")
        df_display = df_year[['country', 'co2']].copy()
        df_display['co2'] = df_display['co2'].apply(lambda x: f"{x:,.0f}")
        df_display['Ranking'] = range(1, len(df_display) + 1)
        df_display = df_display[['Ranking', 'country', 'co2']]
        df_display.columns = ['Ranking', 'País', 'Emisiones (toneladas)']
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True
        )
        
        # Gráfico de barras
        fig = px.bar(
            df_year,
            x='co2',
            y='country',
            orientation='h',
            title=f"Top {top_n} países por emisiones de CO₂ en {selected_year}",
            labels={
                'co2': 'CO₂ (toneladas)',
                'country': 'País'
            },
            color='co2',
            color_continuous_scale='Reds'
        )
        fig.update_layout(
            template='plotly_white',
            yaxis={'categoryorder': 'total ascending'},
            height=600,
            xaxis_title="Emisiones de CO₂ (toneladas)",
            yaxis_title="País",
            showlegend=False
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        st.plotly_chart(fig, use_container_width=True)
        
        # Análisis interpretativo
        with st.expander("Análisis e Interpretación", expanded=False):
            top_country = df_year.iloc[0]['country']
            top_value = df_year.iloc[0]['co2']
            st.markdown(f"""
            **Observaciones para {selected_year}:**
            - **Mayor emisor:** {top_country} con {top_value:,.0f} toneladas de CO₂
            - **Top {top_n} países concentran:** {percentage:.1f}% de las emisiones globales
            - **Diferencia entre 1° y {top_n}°:** {df_year.iloc[0]['co2'] - df_year.iloc[-1]['co2']:,.0f} toneladas
            
            **Interpretación:** {'Los países del top ' + str(top_n) + ' concentran una proporción ' + ('muy alta' if percentage > 70 else 'alta' if percentage > 50 else 'moderada') + ' de las emisiones globales.'} 
            Esto indica una {'alta' if percentage > 70 else 'moderada'} concentración de emisiones en un grupo reducido de países.
            """)
    else:
        st.warning(f"No hay datos disponibles para el año {selected_year}")

# ============================================
# TAB 3: EMISIONES ACUMULADAS
# ============================================
with tab3:
    st.header("Emisiones Acumuladas de CO₂")
    st.markdown("""
    **Visualización:** Gráfico de área  
    **Marca:** Área bajo curva  
    **Canal visual:** Área (magnitud acumulada), posición en eje X (tiempo)  
    **Justificación:** El gráfico de área enfatiza la acumulación total de emisiones a lo largo del tiempo. 
    El área bajo la curva representa visualmente la contribución histórica total de un país a las emisiones globales.
    """)
    
    selected_country_cum = st.selectbox(
        "Selecciona un país:",
        options=countries,
        index=countries.index('United States') if 'United States' in countries else 0,
        key="country_cumulative"
    )
    
    # Calcular emisiones acumuladas
    subset_cum = df[df['country'] == selected_country_cum].sort_values('year')
    subset_cum = subset_cum.dropna(subset=['co2'])
    subset_cum = subset_cum.copy()
    subset_cum['cumulative'] = subset_cum['co2'].cumsum()
    subset_cum['annual'] = subset_cum['co2']
    
    if len(subset_cum) > 0:
        total_cumulative = subset_cum['cumulative'].max()
        avg_annual = subset_cum['co2'].mean()
        max_annual = subset_cum['co2'].max()
        max_annual_year = subset_cum.loc[subset_cum['co2'].idxmax(), 'year']
        
        # Mostrar métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Emisiones totales acumuladas", f"{total_cumulative:,.0f} ton")
        with col2:
            st.metric("Emisiones promedio anual", f"{avg_annual:,.0f} ton")
        with col3:
            st.metric("Emisiones máximas anuales", f"{max_annual:,.0f} ton")
        with col4:
            st.metric("Año de máximo", f"{int(max_annual_year)}")
        
        # Gráfico de área acumulada
        fig = px.area(
            subset_cum,
            x='year',
            y='cumulative',
            title=f"Emisiones acumuladas de CO₂ — {selected_country_cum}",
            labels={
                'cumulative': 'CO₂ acumulado (toneladas)',
                'year': 'Año'
            },
            color_discrete_sequence=['#ef553b']
        )
        fig.update_layout(
            template='plotly_white',
            height=500,
            xaxis_title="Año",
            yaxis_title="CO₂ acumulado (toneladas)",
            hovermode='x unified'
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        st.plotly_chart(fig, use_container_width=True)
        
        # Análisis interpretativo
        with st.expander("Análisis e Interpretación", expanded=False):
            st.markdown(f"""
            **Observaciones para {selected_country_cum}:**
            - **Contribución histórica total:** {total_cumulative:,.0f} toneladas de CO₂ acumuladas
            - **Emisiones promedio anual:** {avg_annual:,.0f} toneladas
            - **Año de mayor emisión anual:** {int(max_annual_year)} con {max_annual:,.0f} toneladas
            
            **Interpretación:** {'Las emisiones acumuladas muestran una contribución histórica ' + ('muy significativa' if total_cumulative > 100000000 else 'significativa' if total_cumulative > 10000000 else 'moderada') + ' a las emisiones globales.'} 
            El patrón de acumulación {'muestra un crecimiento acelerado' if subset_cum['co2'].iloc[-10:].mean() > subset_cum['co2'].iloc[:10].mean() * 2 else 'muestra estabilidad' if abs(subset_cum['co2'].iloc[-10:].mean() - subset_cum['co2'].iloc[:10].mean()) / subset_cum['co2'].iloc[:10].mean() < 0.2 else 'muestra variabilidad'} 
            a lo largo del tiempo.
            """)
    else:
        st.warning(f"No hay datos disponibles para {selected_country_cum}")

# ============================================
# TAB 4: TENDENCIA GLOBAL + TOP 10
# ============================================
with tab4:
    st.header("Tendencia Global y Comparación con Top Países")
    st.markdown("""
    **Visualización:** Múltiples líneas temporales  
    **Marca:** Líneas de diferentes colores  
    **Canal visual:** Posición Y (magnitud), color (identificación de país), posición X (tiempo)  
    **Justificación:** Las líneas múltiples permiten comparar simultáneamente la tendencia global con países individuales. 
    El color diferencia cada entidad, mientras que la posición vertical permite comparar magnitudes relativas.
    """)
    
    # Calcular tendencia global
    global_trend = (
        df.groupby('year', as_index=False)['co2']
          .sum()
          .rename(columns={'co2': 'co2_global'})
    )
    global_trend['country'] = 'Mundo (Total Global)'
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
    df_display = country_totals.head(10)[['country', 'co2']].copy()
    df_display['co2'] = df_display['co2'].apply(lambda x: f"{x:,.0f}")
    df_display['Ranking'] = range(1, len(df_display) + 1)
    df_display = df_display[['Ranking', 'country', 'co2']]
    df_display.columns = ['Ranking', 'País', 'Emisiones Totales (toneladas)']
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )
    
    # Calcular porcentaje del top 10
    total_top10 = country_totals.head(10)['co2'].sum()
    total_global_all = df['co2'].sum()
    percentage_top10 = (total_top10 / total_global_all * 100) if total_global_all > 0 else 0
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Emisiones totales Top 10", f"{total_top10:,.0f} ton")
    with col2:
        st.metric("Porcentaje del total histórico", f"{percentage_top10:.1f}%")
    
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
            'country': 'País/Región'
        }
    )
    fig.update_layout(
        template='plotly_white',
        height=600,
        xaxis_title="Año",
        yaxis_title="CO₂ (toneladas)",
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )
    fig.update_traces(line=dict(width=2))
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    st.plotly_chart(fig, use_container_width=True)
    
    # Análisis interpretativo
    with st.expander("Análisis e Interpretación", expanded=False):
        st.markdown(f"""
        **Observaciones globales:**
        - **Top 10 países concentran:** {percentage_top10:.1f}% de las emisiones históricas totales
        - **Tendencia global:** {'Crecimiento continuo' if global_trend['co2'].iloc[-1] > global_trend['co2'].iloc[0] * 1.5 else 'Estabilidad relativa' if abs(global_trend['co2'].iloc[-1] - global_trend['co2'].iloc[0]) / global_trend['co2'].iloc[0] < 0.3 else 'Variabilidad'}
        - **Emisiones globales actuales:** {global_trend['co2'].iloc[-1]:,.0f} toneladas
        
        **Interpretación:** La concentración de emisiones en el top 10 países ({percentage_top10:.1f}%) indica una 
        {'alta' if percentage_top10 > 70 else 'moderada' if percentage_top10 > 50 else 'baja'} desigualdad en la distribución 
        de emisiones a nivel global. La tendencia global muestra {'un crecimiento sostenido' if global_trend['co2'].iloc[-10:].mean() > global_trend['co2'].iloc[:10].mean() * 1.5 else 'una estabilización' if abs(global_trend['co2'].iloc[-10:].mean() - global_trend['co2'].iloc[:10].mean()) / global_trend['co2'].iloc[:10].mean() < 0.2 else 'variaciones significativas'} 
        en las emisiones a lo largo del tiempo.
        """)

# ============================================
# TAB 5: MAPA ANIMADO
# ============================================
with tab5:
    st.header("Mapa Animado de Emisiones de CO₂")
    st.markdown("""
    **Visualización:** Mapa coroplético animado  
    **Marca:** Regiones geográficas coloreadas  
    **Canal visual:** Color (intensidad de emisiones), posición geográfica (ubicación), tiempo (animación)  
    **Justificación:** El mapa coroplético permite visualizar patrones espaciales y temporales simultáneamente. 
    El color codifica la magnitud de emisiones, facilitando la identificación de regiones de alto/bajo impacto. 
    La animación temporal revela cambios geográficos en las emisiones a lo largo del tiempo.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Selecciona un año específico o usa la animación:**")
    
    with col2:
        use_animation = st.checkbox("Usar animación", value=True)
    
    # Preparar datos para el mapa
    df_map = df[df['code'].str.len() == 3].copy()
    df_map = df_map.dropna(subset=['co2'])
    df_map = df_map.sort_values(by='year')
    
    if use_animation:
        # Crear mapa animado
        fig_map_anim = px.choropleth(
            df_map,
            locations='code',
            color='co2',
            hover_name='country',
            animation_frame='year',
            color_continuous_scale='Reds',
            projection='natural earth',
            title='Mapa animado de emisiones anuales de CO₂ (1750-2024)',
            labels={'co2': 'CO₂ (toneladas)', 'year': 'Año'}
        )
        
        fig_map_anim.update_geos(
            showcountries=True, 
            showcoastlines=True,
            showframe=False,
            bgcolor='rgba(0,0,0,0)'
        )
        fig_map_anim.update_layout(
            height=700,
            coloraxis=dict(colorbar=dict(title="CO₂ (toneladas)"))
        )
        
        # Ajustar velocidad de animación
        if len(fig_map_anim.layout.updatemenus) > 0:
            fig_map_anim.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 150
            fig_map_anim.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 50
        
        st.plotly_chart(fig_map_anim, use_container_width=True)
        st.info("Usa los controles de reproducción en el mapa para animar la visualización temporal")
    else:
        # Mapa estático para un año específico
        selected_year_map = st.slider(
            "Selecciona un año:",
            min_value=int(years[0]),
            max_value=int(years[-1]),
            value=int(years[-1]),
            step=1,
            key="year_map"
        )
        
        df_map_year = df_map[df_map['year'] == selected_year_map].copy()
        
        fig_map_static = px.choropleth(
            df_map_year,
            locations='code',
            color='co2',
            hover_name='country',
            color_continuous_scale='Reds',
            projection='natural earth',
            title=f'Mapa de emisiones de CO₂ en {selected_year_map}',
            labels={'co2': 'CO₂ (toneladas)'}
        )
        
        fig_map_static.update_geos(
            showcountries=True, 
            showcoastlines=True,
            showframe=False,
            bgcolor='rgba(0,0,0,0)'
        )
        fig_map_static.update_layout(
            height=700,
            coloraxis=dict(colorbar=dict(title="CO₂ (toneladas)"))
        )
        
        st.plotly_chart(fig_map_static, use_container_width=True)
        
        # Estadísticas del año seleccionado
        if len(df_map_year) > 0:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Países con datos", len(df_map_year))
            with col2:
                st.metric("Total global", f"{df_map_year['co2'].sum():,.0f} ton")
            with col3:
                st.metric("Promedio por país", f"{df_map_year['co2'].mean():,.0f} ton")
    
    # Análisis interpretativo
    with st.expander("Análisis e Interpretación", expanded=False):
        st.markdown("""
        **Observaciones del mapa:**
        - **Patrón geográfico:** Las emisiones muestran una distribución desigual a nivel global
        - **Evolución temporal:** La animación revela cambios en la geografía de las emisiones
        - **Concentración regional:** Ciertas regiones mantienen altos niveles de emisiones históricamente
        
        **Interpretación:** El mapa coroplético permite identificar visualmente:
        1. **Regiones de alto impacto:** Áreas con colores más intensos (rojos oscuros)
        2. **Cambios temporales:** Cómo se desplazan los focos de emisión a lo largo del tiempo
        3. **Desigualdad espacial:** La concentración geográfica de emisiones refleja patrones de desarrollo económico e industrial
        
        La visualización espacial complementa los análisis temporales y de ranking, proporcionando una perspectiva 
        geográfica única sobre la distribución global de emisiones de CO₂.
        """)

# ============================================
# SECCIÓN DE METODOLOGÍA Y DECISIONES DE DISEÑO
# ============================================
st.markdown("---")
with st.expander("Metodología y Decisiones de Diseño", expanded=False):
    st.markdown("""
    ### Justificación Técnica de las Visualizaciones
    
    #### 1. Serie Temporal (Línea)
    - **Marca:** Línea continua
    - **Canales:** Posición Y (magnitud), Posición X (tiempo)
    - **Razón:** Permite identificar tendencias, quiebres y patrones de crecimiento/declive de manera efectiva
    
    #### 2. Ranking por Año (Barras Horizontales)
    - **Marca:** Barras rectangulares
    - **Canales:** Longitud (magnitud), Posición vertical (ranking)
    - **Razón:** Facilita la lectura de nombres y comparación de magnitudes entre países
    
    #### 3. Emisiones Acumuladas (Área)
    - **Marca:** Área bajo curva
    - **Canales:** Área (magnitud acumulada), Posición X (tiempo)
    - **Razón:** Enfatiza la contribución histórica total, visualizando el impacto acumulado
    
    #### 4. Tendencia Global (Múltiples Líneas)
    - **Marca:** Líneas de diferentes colores
    - **Canales:** Posición Y (magnitud), Color (identificación), Posición X (tiempo)
    - **Razón:** Permite comparación simultánea entre tendencia global y países individuales
    
    #### 5. Mapa Coroplético (Geografía)
    - **Marca:** Regiones geográficas coloreadas
    - **Canales:** Color (intensidad), Posición geográfica (ubicación), Tiempo (animación)
    - **Razón:** Revela patrones espaciales y cambios geográficos en las emisiones
    
    ### Limitaciones y Consideraciones
    - Los datos representan emisiones **territoriales** (dentro de fronteras), no incluyen emisiones de bienes importados
    - No incluyen emisiones de aviación/shipping internacional
    - Algunos países pueden tener datos incompletos en ciertos períodos
    - Las escalas de color pueden variar entre visualizaciones para optimizar la legibilidad
    """)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; padding: 20px;'>
        <p><strong>Visualización de Emisiones de CO₂ Global</strong></p>
        <p>Datos: <a href='https://ourworldindata.org' target='_blank'>Our World in Data</a> - Global Carbon Budget</p>
        <p style='font-size: 0.9em;'>Desarrollado con Streamlit y Plotly</p>
    </div>
    """,
    unsafe_allow_html=True
)

