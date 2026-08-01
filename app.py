import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re

# 1. CONFIGURACIÓN DE RUTAS
LOGO_PATH = "07.jpeg"  #---->ruta del logo   

COLOR_PRIMARIO = "#7bc11d" 
COLOR_SECUNDARIO = "#267e26" 

st.set_page_config(page_title="Metrix Dashboard", layout="wide")

# CSS para adaptar los colores Y OCULTAR EL MENÚ DE STREAMLIT
st.markdown(f"""
<style>
    /*OCULTAN EL MENÚ Y LOGOS DE GITHUB/STREAMLIT */
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* Fondo de la app */
    .stApp {{ background-color: #050505; }}
    
    /* Diseño de las tarjetas de KPIs */
    div[data-testid="stMetric"] {{
        background-color: #0a110a;
        border: 1px solid {COLOR_PRIMARIO};
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(123, 193, 29, 0.15);
    }}
    
    /* Textos y títulos */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"], h1, h2, h3 {{
        color: {COLOR_PRIMARIO} !important; 
        font-family: 'Courier New', monospace;
    }}
    
    hr {{ border-bottom-color: {COLOR_SECUNDARIO} !important; opacity: 0.5; }}
</style>
""", unsafe_allow_html=True)

st.title("Panel de Desarrollo")
st.markdown("---")

# 2. CARGA Y LIMPIEZA DE DATOS
@st.cache_data
def cargar_datos():
    nombre_archivo = "planeacion.xlsx" #---->ruta del archivo Excel
    try:
        df = pd.read_excel(nombre_archivo)
        
        # Función para limpiar y calcular horas
        def interpretar_tiempo(val):
            if pd.isna(val) or val == '?':
                return 0.0
            
            val_str = str(val).lower().strip()
            # Extraer el número
            match = re.search(r'([0-9]*\.?[0-9]+)', val_str)
            if not match:
                return 0.0
                
            num = float(match.group(1))
            
            # Conversiones
            if 'min' in val_str:
                return num / 60.0       # Convierte minutos a horas
            elif 'dia' in val_str or 'día' in val_str:
                return num * 8.0        # Multiplica días por 8 horas (Jornada laboraL)
            else:
                return num              # Si ya está en horas, se queda igual
                
        df["Estimación Horas"] = df["Estimación Horas"].apply(interpretar_tiempo)
        df["Avance %"] = pd.to_numeric(df["Avance %"], errors="coerce").fillna(0) * 100
        
        return df
        
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo '{nombre_archivo}'")
        st.info("Asegúrate de que el Excel esté guardado en la misma carpeta que 'app.py' y que el nombre sea idéntico.")
        st.stop()

df = cargar_datos()

# 3. BARRA LATERAL (LOGO Y FILTROS)
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.info(f"🖼️ Espacio para Logo: Coloca tu imagen en '{LOGO_PATH}'")
        
    st.markdown("---")
    
    clientes = st.multiselect("Cliente:", df["Cliente"].dropna().unique())
    resp = st.multiselect("Responsable:", df["Responsable"].dropna().unique())
    estatus = st.multiselect("Estatus:", df["Estatus"].dropna().unique())

df_filt = df.copy()
if clientes: df_filt = df_filt[df_filt["Cliente"].isin(clientes)]
if resp:     df_filt = df_filt[df_filt["Responsable"].isin(resp)]
if estatus:  df_filt = df_filt[df_filt["Estatus"].isin(estatus)]

# 4. TARJETAS DE KPIs 
c1, c2, c3, c4, c5 = st.columns(5)

total_actividades = len(df_filt)
horas_totales = df_filt['Estimación Horas'].sum()
promedio_horas_act = (horas_totales / total_actividades) if total_actividades > 0 else 0

c1.metric("Total Actividades", total_actividades)
c2.metric("Horas Estimadas", f"{horas_totales:,.1f} h")
c3.metric("Promedio Hrs/Actividad", f"{promedio_horas_act:.1f} h")
c4.metric("Avance Global", f"{df_filt['Avance %'].mean():.1f}%" if not df_filt.empty else "0%")
c5.metric("Completadas (100%)", len(df_filt[df_filt["Avance %"] == 100]))

st.markdown("<br>", unsafe_allow_html=True)

# 5. GRÁFICOS
g1, g2 = st.columns(2)

graf_config = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=COLOR_PRIMARIO))
colores_graficas = [COLOR_PRIMARIO, COLOR_SECUNDARIO, "#ffffff", "#555555", "#111111"]

with g1:
    fig1 = px.pie(df_filt, names="Estatus", title="Distribución por Estatus", hole=0.4, color_discrete_sequence=colores_graficas)
    fig1.update_layout(**graf_config)
    st.plotly_chart(fig1, use_container_width=True)

with g2:
    horas_resp = df_filt.groupby("Responsable")["Estimación Horas"].sum().reset_index()
    fig2 = px.bar(horas_resp, x="Responsable", y="Estimación Horas", title="Horas por Responsable", color_discrete_sequence=[COLOR_PRIMARIO])
    fig2.update_layout(**graf_config)
    fig2.update_yaxes(showgrid=True, gridcolor=COLOR_SECUNDARIO) 
    st.plotly_chart(fig2, use_container_width=True)

# 6. TABLA DE DATOS
st.markdown("### Detalle de Actividades")
st.dataframe(
    df_filt[["Cliente", "Módulo", "Responsable", "Estatus", "Estimación Horas", "Avance %"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Avance %": st.column_config.ProgressColumn("Avance (%)", format="%d%%", min_value=0, max_value=100)
    }
)
