import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re

# ==========================================
# 1. CONFIGURACIÓN DE RUTAS Y COLORES
# ==========================================
# Coloca aquí tu archivo PNG original con fondo transparente
LOGO_PATH = "08.png"  

COLOR_PRIMARIO = "#7bc11d" 
COLOR_SECUNDARIO = "#267e26" 

st.set_page_config(page_title="Metrix Dashboard", layout="wide", initial_sidebar_state="collapsed")

# CSS Avanzado para diseño limpio y compacto
st.markdown(f"""
<style>
    /* Ocultar botones de Streamlit para no verse expuesto */
    [data-testid="stHeaderActionElements"] {{ display: none !important; }}
    [data-testid="collapsedControl"] {{ display: none !important; }}
    footer {{ visibility: hidden !important; }}
    header {{ background: transparent !important; }}

    /* Ajuste extremo de márgenes para maximizar espacio (elimina la caja azul) */
    .block-container {{
        padding-top: 2rem !important; 
        padding-bottom: 2rem !important;
        max-width: 95%;
    }}

    /* Diseño de las tarjetas de KPIs */
    div[data-testid="stMetric"] {{
        background-color: var(--secondary-background-color); 
        border-left: 4px solid {COLOR_PRIMARIO}; 
        padding: 15px 20px; 
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }}
    
    [data-testid="stMetricValue"] {{
        color: {COLOR_PRIMARIO} !important; 
        font-family: 'Courier New', monospace;
        font-size: 2rem !important;
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 1.1rem !important;
        font-weight: 600;
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CARGA Y LIMPIEZA DE DATOS
# ==========================================
@st.cache_data
def cargar_datos():
    nombre_archivo = "planeacion.xlsx" 
    try:
        df = pd.read_excel(nombre_archivo)
        
        def interpretar_tiempo(val):
            if pd.isna(val) or val == '?': return 0.0
            val_str = str(val).lower().strip()
            match = re.search(r'([0-9]*\.?[0-9]+)', val_str)
            if not match: return 0.0
            num = float(match.group(1))
            
            if 'min' in val_str: return num / 60.0       
            elif 'dia' in val_str or 'día' in val_str: return num * 8.0        
            else: return num              
                
        df["Estimación Horas"] = df["Estimación Horas"].apply(interpretar_tiempo)
        df["Avance %"] = pd.to_numeric(df["Avance %"], errors="coerce").fillna(0) * 100
        df["Fecha de Inicio"] = pd.to_datetime(df["Fecha de Inicio"], errors="coerce")
        df["Fecha de Entrega"] = pd.to_datetime(df["Fecha de Entrega"], errors="coerce")
        
        return df
    except FileNotFoundError:
        st.error(f"🚨 Error: No se encontró el archivo '{nombre_archivo}'")
        st.stop()

df = cargar_datos()

# ==========================================
# 3. ENCABEZADO Y LOGO (Diseño Compacto)
# ==========================================
# Se ajustan las proporciones para que el logo no ocupe demasiado espacio a lo ancho
col_logo, col_titulo = st.columns([1, 8])

with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.info(f"🖼️ Sube: {LOGO_PATH}")

with col_titulo:
    st.markdown(f"<h1 style='color: {COLOR_SECUNDARIO}; margin-top: -15px; margin-bottom: 0; padding-bottom: 0;'>🚀 Panel de Desarrollo Metrix</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: gray; font-size: 1.1em; margin-top: 0; margin-bottom: 15px;'>Sistema centralizado de control de tiempos, recursos y estatus de proyectos.</p>", unsafe_allow_html=True)

# 🛑 Se eliminó la línea divisoria (st.markdown("---")) para aprovechar el espacio azul.

# ==========================================
# 4. PANEL DE CONTROL (FILTROS PEGADOS AL ENCABEZADO)
# ==========================================
f1, f2, f3 = st.columns(3)

with f1:
    clientes = st.multiselect("👥 Filtrar por Cliente:", df["Cliente"].dropna().unique())
with f2:
    resp = st.multiselect("🧑‍💻 Filtrar por Responsable:", df["Responsable"].dropna().unique())
with f3:
    estatus = st.multiselect("📌 Filtrar por Estatus:", df["Estatus"].dropna().unique())

df_filt = df.copy()
if clientes: df_filt = df_filt[df_filt["Cliente"].isin(clientes)]
if resp:     df_filt = df_filt[df_filt["Responsable"].isin(resp)]
if estatus:  df_filt = df_filt[df_filt["Estatus"].isin(estatus)]

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 5. TARJETAS DE KPIs
# ==========================================
c1, c2, c3 = st.columns(3)
c4, c5, c6 = st.columns(3)

total_actividades = len(df_filt)
horas_totales = df_filt['Estimación Horas'].sum()
promedio_horas_act = (horas_totales / total_actividades) if total_actividades > 0 else 0
hoy = pd.Timestamp.now().normalize()
actividades_atrasadas = len(df_filt[(df_filt["Fecha de Entrega"] < hoy) & (df_filt["Avance %"] < 100)])

c1.metric("📋 Total Tareas", total_actividades)
c2.metric("⏱️ Horas Estimadas", f"{horas_totales:,.1f} h")
c3.metric("⚖️ Promedio Hrs/Tarea", f"{promedio_horas_act:.1f} h")

c4.metric("📈 Avance Global", f"{df_filt['Avance %'].mean():.1f}%" if not df_filt.empty else "0%")
c5.metric("✅ Tareas Completadas", len(df_filt[df_filt["Avance %"] == 100]))
c6.metric("🚨 Tareas Atrasadas", actividades_atrasadas) 

st.markdown("---")

# ==========================================
# 6. GRÁFICOS ANALÍTICOS
# ==========================================
g1, g2 = st.columns(2)
graf_config = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
colores_graficas = [COLOR_PRIMARIO, COLOR_SECUNDARIO, "#888888", "#cccccc", "#222222"]

with g1:
    st.markdown("#### 📊 Distribución del Proyecto")
    fig1 = px.pie(df_filt, names="Estatus", hole=0.4, color_discrete_sequence=colores_graficas)
    fig1.update_layout(**graf_config, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig1, use_container_width=True)

with g2:
    st.markdown("#### 🧑‍💻 Carga Horaria por Desarrollador")
    horas_resp = df_filt.groupby("Responsable")["Estimación Horas"].sum().reset_index()
    fig2 = px.bar(horas_resp, x="Responsable", y="Estimación Horas", color_discrete_sequence=[COLOR_PRIMARIO])
    fig2.update_layout(**graf_config, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig2, use_container_width=True)

# ==========================================
# 7. DIAGRAMA DE GANTT
# ==========================================
st.markdown("---")
st.markdown("### 📅 Cronograma de Ejecución (Gantt)")

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
    fig_gantt.update_layout(**graf_config, xaxis_title="", yaxis_title="")
    st.plotly_chart(fig_gantt, use_container_width=True)
else:
    st.info("💡 Faltan fechas de Inicio/Entrega para generar el diagrama de Gantt.")

# ==========================================
# 8. TABLA DE DATOS
# ==========================================
st.markdown("---")
st.markdown("### Matriz de Actividades")
st.dataframe(
    df_filt[["Cliente", "Módulo", "Responsable", "Estatus", "Estimación Horas", "Avance %", "Fecha de Entrega"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Avance %": st.column_config.ProgressColumn("Avance (%)", format="%d%%", min_value=0, max_value=100),
        "Fecha de Entrega": st.column_config.DateColumn("Fecha Entrega", format="DD/MM/YYYY")
    }
)
