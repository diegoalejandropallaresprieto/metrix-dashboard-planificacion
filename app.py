import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re
import base64
from datetime import datetime

# 1. CONFIGURACIÓN DE RUTAS Y COLORES
BANNER_PATH = "07.jpeg"  # ----> Ruta de tu imagen para el banner translúcido

COLOR_PRIMARIO = "#7bc11d" 
COLOR_SECUNDARIO = "#267e26" 
COLOR_TEXTO = "#333333"

st.set_page_config(page_title="Metrix Dashboard", layout="wide")

# CSS para adaptar los colores, espacios y traslucidez
st.markdown(f"""
<style>
    /* Ajuste de margen superior para dar respiro (ya no está pegado arriba) */
    .block-container {{
        padding-top: 4rem !important; 
        padding-bottom: 2rem !important;
    }}

    /* Diseño de las tarjetas de KPIs - Más amplias y separadas */
    div[data-testid="stMetric"] {{
        background-color: var(--secondary-background-color); 
        border: 1px solid {COLOR_PRIMARIO};
        padding: 20px; /* Más espacio interno */
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 1rem; /* Separación entre filas */
    }}
    
    /* Textos adaptables */
    [data-testid="stMetricValue"] {{
        color: {COLOR_PRIMARIO} !important; 
        font-family: 'Courier New', monospace;
    }}
    [data-testid="stMetricLabel"] {{
        color: var(--text-color) !important; 
        font-weight: bold;
    }}
    h1, h2, h3 {{
        color: {COLOR_SECUNDARIO} !important; 
    }}
    
    hr {{ border-bottom-color: {COLOR_PRIMARIO} !important; opacity: 0.3; }}
    
    /* Clase CSS para el banner translúcido */
    .banner-translucido {{
        opacity: 0.6; /* Nivel de traslucidez (0.0 es invisible, 1.0 es sólido) */
        border-radius: 10px;
        width: 100%;
        max-height: 250px;
        object-fit: cover;
        margin-bottom: 2rem;
    }}
</style>
""", unsafe_allow_html=True)

# 2. BANNER TRANSLÚCIDO
if os.path.exists(BANNER_PATH):
    # Convertimos la imagen a código para poder inyectarle el CSS de traslucidez directamente
    with open(BANNER_PATH, "rb") as image_file:
        img_base64 = base64.b64encode(image_file.read()).decode()
    st.markdown(f'<img src="data:image/jpeg;base64,{img_base64}" class="banner-translucido">', unsafe_allow_html=True)
else:
    st.info(f"🖼️ Espacio para Banner Translúcido: Guarda tu imagen como '{BANNER_PATH}' en esta misma carpeta.")

st.title("Panel de Desarrollo")
st.markdown("---")

# 3. CARGA Y LIMPIEZA DE DATOS
@st.cache_data
def cargar_datos():
    nombre_archivo = "planeacion.xlsx" #---->ruta del archivo Excel
    try:
        df = pd.read_excel(nombre_archivo)
        
        def interpretar_tiempo(val):
            if pd.isna(val) or val == '?':
                return 0.0
            
            val_str = str(val).lower().strip()
            match = re.search(r'([0-9]*\.?[0-9]+)', val_str)
            if not match:
                return 0.0
                
            num = float(match.group(1))
            
            if 'min' in val_str:
                return num / 60.0       
            elif 'dia' in val_str or 'día' in val_str:
                return num * 8.0        
            else:
                return num              
                
        df["Estimación Horas"] = df["Estimación Horas"].apply(interpretar_tiempo)
        df["Avance %"] = pd.to_numeric(df["Avance %"], errors="coerce").fillna(0) * 100
        
        df["Fecha de Inicio"] = pd.to_datetime(df["Fecha de Inicio"], errors="coerce")
        df["Fecha de Entrega"] = pd.to_datetime(df["Fecha de Entrega"], errors="coerce")
        
        return df
        
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo '{nombre_archivo}'")
        st.stop()

df = cargar_datos()

# 4. BARRA LATERAL (LOGO EN TEXTO Y FILTROS)
with st.sidebar:
    # Logo tipográfico en lugar de imagen
    st.markdown(f"<h1 style='text-align: center; color: {COLOR_PRIMARIO}; font-family: Courier New, monospace; letter-spacing: 2px;'>MX METRIX</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    clientes = st.multiselect("Cliente:", df["Cliente"].dropna().unique())
    resp = st.multiselect("Responsable:", df["Responsable"].dropna().unique())
    estatus = st.multiselect("Estatus:", df["Estatus"].dropna().unique())

df_filt = df.copy()
if clientes: df_filt = df_filt[df_filt["Cliente"].isin(clientes)]
if resp:     df_filt = df_filt[df_filt["Responsable"].isin(resp)]
if estatus:  df_filt = df_filt[df_filt["Estatus"].isin(estatus)]

# 5. TARJETAS DE KPIs (Ahora divididas en 2 filas para mayor amplitud)
# Fila 1
c1, c2, c3 = st.columns(3)
# Fila 2
c4, c5, c6 = st.columns(3)

total_actividades = len(df_filt)
horas_totales = df_filt['Estimación Horas'].sum()
promedio_horas_act = (horas_totales / total_actividades) if total_actividades > 0 else 0

hoy = pd.Timestamp.now().normalize()
actividades_atrasadas = len(df_filt[(df_filt["Fecha de Entrega"] < hoy) & (df_filt["Avance %"] < 100)])

c1.metric("Total Actividades", total_actividades)
c2.metric("Horas Estimadas", f"{horas_totales:,.1f} h")
c3.metric("Prom Hrs/Act", f"{promedio_horas_act:.1f} h")

c4.metric("Avance Global", f"{df_filt['Avance %'].mean():.1f}%" if not df_filt.empty else "0%")
c5.metric("Completadas", len(df_filt[df_filt["Avance %"] == 100]))
c6.metric("🚨 Atrasadas", actividades_atrasadas) 

st.markdown("<br>", unsafe_allow_html=True)

# 6. GRÁFICOS 
g1, g2 = st.columns(2)

graf_config = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=COLOR_TEXTO))
colores_graficas = [COLOR_PRIMARIO, COLOR_SECUNDARIO, "#888888", "#cccccc", "#222222"]

with g1:
    fig1 = px.pie(df_filt, names="Estatus", title="Distribución por Estatus", hole=0.4, color_discrete_sequence=colores_graficas)
    fig1.update_layout(**graf_config)
    st.plotly_chart(fig1, use_container_width=True)

with g2:
    horas_resp = df_filt.groupby("Responsable")["Estimación Horas"].sum().reset_index()
    fig2 = px.bar(horas_resp, x="Responsable", y="Estimación Horas", title="Horas por Responsable", color_discrete_sequence=[COLOR_PRIMARIO])
    fig2.update_layout(**graf_config)
    fig2.update_yaxes(showgrid=True, gridcolor="#e0e0e0") 
    st.plotly_chart(fig2, use_container_width=True)

# 7. DIAGRAMA DE GANTT (Vista Temporal)
st.markdown("---")
st.subheader("Cronograma de Actividades (Gantt)")

df_gantt = df_filt.dropna(subset=["Fecha de Inicio", "Fecha de Entrega"])

if not df_gantt.empty:
    fig_gantt = px.timeline(
        df_gantt, 
        x_start="Fecha de Inicio", 
        x_end="Fecha de Entrega", 
        y="Responsable", 
        color="Estatus",
        hover_name="Módulo",
        color_discrete_sequence=colores_graficas
    )
    fig_gantt.update_yaxes(autorange="reversed")
    fig_gantt.update_layout(
        **graf_config,
        xaxis_title="Timeline",
        yaxis_title="Responsable",
        showlegend=True
    )
    fig_gantt.update_xaxes(showgrid=True, gridcolor="#e0e0e0")
    st.plotly_chart(fig_gantt, use_container_width=True)
else:
    st.info("💡 No hay suficientes datos de fechas (Inicio / Entrega) en el archivo para generar el diagrama de Gantt.")

# 8. TABLA DE DATOS
st.markdown("---")
st.subheader("Detalle de Actividades")
st.dataframe(
    df_filt[["Cliente", "Módulo", "Responsable", "Estatus", "Estimación Horas", "Avance %", "Fecha de Entrega"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Avance %": st.column_config.ProgressColumn("Avance (%)", format="%d%%", min_value=0, max_value=100),
        "Fecha de Entrega": st.column_config.DateColumn("Fecha Entrega", format="DD/MM/YYYY")
    }
)
