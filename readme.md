# Visualización de Emisiones de CO₂ Global

Aplicación web interactiva desarrollada con Streamlit para visualizar y analizar las emisiones de CO₂ por país a lo largo del tiempo.

## Descripción

Esta aplicación convierte el análisis del notebook de Jupyter en una aplicación web interactiva que permite:

-  Visualizar series temporales de emisiones por país
-  Explorar rankings de países por año
-  Analizar emisiones acumuladas
-  Comparar tendencias globales con los top 10 países
-  Explorar un mapa animado de emisiones

##  Instalación

### Requisitos previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de instalación

1. **Clonar o descargar el repositorio**

```bash
git clone <url-del-repositorio>
cd udd_visualizacion_datos_test_streamlit
```

2. **Crear un entorno virtual (recomendado)**

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

3. **Instalar las dependencias**

```bash
pip install -r requirements.txt
```

## 📁 Estructura de Datos

Asegúrate de que los archivos de datos estén organizados de la siguiente manera:

```
udd_visualizacion_datos_test_streamlit/
├── app.py
├── requirements.txt
├── README.md
└── data/
    ├── ne_50m_admin_0_countries/
    │   └── ne_50m_admin_0_countries.shp
    └── annual-co2-emissions-per-country.csv
```

**Nota:** El shapefile de Natural Earth puede incluir varios archivos (.shp, .shx, .dbf, etc.). Todos deben estar en la carpeta `ne_50m_admin_0_countries/`.

## ▶️ Ejecución

Para ejecutar la aplicación, usa el siguiente comando:

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

##  Funcionalidades

### 1. Serie Temporal
- Selecciona cualquier país para ver su evolución de emisiones
- Visualiza métricas clave (emisiones actuales, históricas, máximas)

### 2. Ranking por Año
- Explora el top 15 de países emisores por año
- Usa el slider para navegar entre diferentes años
- Visualiza datos en tabla y gráfico de barras

### 3. Emisiones Acumuladas
- Analiza las emisiones acumuladas de cualquier país
- Visualiza el crecimiento histórico de emisiones

### 4. Tendencia Global
- Compara la tendencia global con los 10 países más emisores
- Explora las diferencias entre países y la tendencia mundial

### 5. Mapa Animado
- Visualiza las emisiones en un mapa mundial interactivo
- Usa la animación para ver la evolución temporal
- Explora diferentes países haciendo hover sobre el mapa







