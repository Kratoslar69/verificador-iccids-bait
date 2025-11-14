"""
Sistema Verificador de ICCIDs BAIT - Interfaz Web
Aplicación Streamlit para gestionar verificaciones de hasta 500,000 ICCIDs
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO
from dotenv import load_dotenv
from supabase import create_client, Client
from verificador_motor import VerificadorICCID
import time

# Configuración de página
st.set_page_config(
    page_title="Verificador ICCIDs BAIT",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cargar variables de entorno
load_dotenv()

# Inicializar Supabase
@st.cache_resource
def init_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    return create_client(url, key)

supabase = init_supabase()

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FFD700;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
    }
    .success-box {
        background-color: #d1fae5;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #10b981;
    }
    .warning-box {
        background-color: #fef3c7;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #f59e0b;
    }
    .error-box {
        background-color: #fee2e2;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ef4444;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<div class="main-header">📱 Sistema Verificador de ICCIDs BAIT</div>', unsafe_allow_html=True)

# Sidebar - Menú de navegación
with st.sidebar:
    st.image("https://mibait.com/static/media/logo-bait.svg", width=150)
    st.title("📋 Menú Principal")
    
    menu_option = st.radio(
        "Selecciona una opción:",
        ["🏠 Dashboard", "📤 Cargar Lote", "▶️ Verificar ICCIDs", 
         "📊 Consultar Resultados", "⚙️ Configuración"]
    )
    
    st.divider()
    st.info("**Capacidad:** 30,000 ICCIDs/día\n\n**Velocidad:** 3 seg/ICCID")

# ==================== DASHBOARD ====================
if menu_option == "🏠 Dashboard":
    st.header("📊 Panel de Control General")
    
    # Obtener estadísticas generales
    try:
        response = supabase.table("verificacion_iccids").select("estatus, lote").execute()
        registros = response.data
        
        if registros:
            df = pd.DataFrame(registros)
            
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total = len(df)
                st.metric("📱 Total ICCIDs", f"{total:,}")
            
            with col2:
                activas = len(df[df['estatus'] == 'ACTIVA'])
                st.metric("✅ Activas", f"{activas:,}", delta=f"{(activas/total*100):.1f}%")
            
            with col3:
                inactivas = len(df[df['estatus'] == 'INACTIVA'])
                st.metric("⭕ Inactivas", f"{inactivas:,}", delta=f"{(inactivas/total*100):.1f}%")
            
            with col4:
                pendientes = len(df[df['estatus'] == 'PENDIENTE'])
                st.metric("⏳ Pendientes", f"{pendientes:,}", delta=f"{(pendientes/total*100):.1f}%")
            
            st.divider()
            
            # Gráfico de distribución por estatus
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Distribución por Estado")
                status_counts = df['estatus'].value_counts()
                st.bar_chart(status_counts)
            
            with col2:
                st.subheader("📦 ICCIDs por Lote")
                lote_counts = df['lote'].value_counts().head(10)
                st.bar_chart(lote_counts)
            
            # Tabla de lotes
            st.divider()
            st.subheader("📋 Resumen por Lotes")
            lotes_stats = df.groupby('lote')['estatus'].value_counts().unstack(fill_value=0)
            st.dataframe(lotes_stats, use_container_width=True)
            
        else:
            st.info("📭 No hay datos disponibles. Comienza cargando un lote de ICCIDs.")
    
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {e}")

# ==================== CARGAR LOTE ====================
elif menu_option == "📤 Cargar Lote":
    st.header("📤 Cargar Nuevo Lote de ICCIDs")
    
    st.markdown("""
    ### 📝 Instrucciones:
    1. Prepara un archivo Excel (.xlsx) con una columna llamada **"ICCID"**
    2. Los ICCIDs pueden estar en formato completo (19-20 dígitos) o solo los últimos 13
    3. El sistema extraerá automáticamente los últimos 13 dígitos sin la F
    4. Asigna un nombre único al lote para identificarlo
    """)
    
    # Formulario de carga
    with st.form("form_cargar_lote"):
        nombre_lote = st.text_input(
            "Nombre del Lote",
            placeholder="Ej: Lote_Enero_2025",
            help="Identificador único para este lote"
        )
        
        archivo_excel = st.file_uploader(
            "Selecciona archivo Excel",
            type=['xlsx', 'xls'],
            help="Archivo con columna 'ICCID'"
        )
        
        submitted = st.form_submit_button("📤 Cargar Lote", use_container_width=True)
        
        if submitted:
            if not nombre_lote:
                st.error("❌ Debes proporcionar un nombre para el lote")
            elif not archivo_excel:
                st.error("❌ Debes seleccionar un archivo Excel")
            else:
                try:
                    # Leer archivo Excel
                    df = pd.read_excel(archivo_excel)
                    
                    # Validar que existe columna ICCID
                    if 'ICCID' not in df.columns:
                        st.error("❌ El archivo debe contener una columna llamada 'ICCID'")
                    else:
                        # Procesar ICCIDs
                        verificador = VerificadorICCID()
                        registros_insertados = 0
                        registros_duplicados = 0
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        total_iccids = len(df)
                        
                        for idx, row in df.iterrows():
                            iccid_completo = str(row['ICCID']).strip()
                            ultimos_13 = verificador.extraer_ultimos_13_digitos(iccid_completo)
                            
                            # Insertar en Supabase
                            try:
                                data = {
                                    "iccid_completo": iccid_completo,
                                    "ultimos_13_digitos": ultimos_13,
                                    "lote": nombre_lote,
                                    "estatus": "PENDIENTE"
                                }
                                
                                supabase.table("verificacion_iccids").insert(data).execute()
                                registros_insertados += 1
                            except Exception:
                                registros_duplicados += 1
                            
                            # Actualizar progreso
                            progress = (idx + 1) / total_iccids
                            progress_bar.progress(progress)
                            status_text.text(f"Procesando: {idx + 1}/{total_iccids}")
                        
                        progress_bar.empty()
                        status_text.empty()
                        
                        # Mostrar resultados
                        st.success(f"✅ Lote cargado exitosamente: **{nombre_lote}**")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📥 Total en archivo", total_iccids)
                        with col2:
                            st.metric("✅ Insertados", registros_insertados)
                        with col3:
                            st.metric("⚠️ Duplicados", registros_duplicados)
                
                except Exception as e:
                    st.error(f"❌ Error al procesar archivo: {e}")

# ==================== VERIFICAR ICCIDs ====================
elif menu_option == "▶️ Verificar ICCIDs":
    st.header("▶️ Iniciar Verificación de ICCIDs")
    
    # Obtener lotes disponibles
    try:
        response = supabase.table("verificacion_iccids").select("lote, estatus").execute()
        df = pd.DataFrame(response.data)
        
        if df.empty:
            st.warning("⚠️ No hay lotes disponibles. Primero carga un lote de ICCIDs.")
        else:
            lotes_disponibles = df['lote'].unique().tolist()
            
            # Formulario de verificación
            with st.form("form_verificar"):
                lote_seleccionado = st.selectbox(
                    "Selecciona el lote a verificar",
                    options=lotes_disponibles
                )
                
                # Mostrar estadísticas del lote
                if lote_seleccionado:
                    lote_df = df[df['lote'] == lote_seleccionado]
                    pendientes = len(lote_df[lote_df['estatus'] == 'PENDIENTE'])
                    
                    st.info(f"📊 **ICCIDs pendientes:** {pendientes:,}")
                    
                    if pendientes > 0:
                        tiempo_estimado = (pendientes * 3) / 60
                        st.info(f"⏱️ **Tiempo estimado:** {tiempo_estimado:.1f} minutos")
                
                limite_verificacion = st.number_input(
                    "Límite de ICCIDs a verificar (0 = todas)",
                    min_value=0,
                    max_value=50000,
                    value=100,
                    step=100,
                    help="Recomendado: 100-500 por sesión"
                )
                
                iniciar = st.form_submit_button("🚀 Iniciar Verificación", use_container_width=True)
                
                if iniciar:
                    if pendientes == 0:
                        st.warning("⚠️ No hay ICCIDs pendientes en este lote")
                    else:
                        st.info("🚀 Iniciando verificación... Esto puede tomar varios minutos.")
                        
                        # Contenedores para progreso
                        progress_bar = st.progress(0)
                        status_container = st.empty()
                        metrics_container = st.empty()
                        
                        # Callback para actualizar progreso
                        stats_temp = {"activas": 0, "inactivas": 0, "errores": 0}
                        
                        def actualizar_progreso(actual, total, estatus, numero):
                            progress = actual / total
                            progress_bar.progress(progress)
                            
                            if estatus == "ACTIVA":
                                stats_temp["activas"] += 1
                            elif estatus == "INACTIVA":
                                stats_temp["inactivas"] += 1
                            else:
                                stats_temp["errores"] += 1
                            
                            status_container.text(f"Procesando: {actual}/{total} ICCIDs")
                            
                            col1, col2, col3 = metrics_container.columns(3)
                            col1.metric("✅ Activas", stats_temp["activas"])
                            col2.metric("⭕ Inactivas", stats_temp["inactivas"])
                            col3.metric("❌ Errores", stats_temp["errores"])
                        
                        # Ejecutar verificación
                        try:
                            verificador = VerificadorICCID()
                            limite = None if limite_verificacion == 0 else limite_verificacion
                            
                            resultados = verificador.procesar_lote(
                                lote_seleccionado,
                                limite=limite,
                                callback_progreso=actualizar_progreso
                            )
                            
                            progress_bar.empty()
                            status_container.empty()
                            
                            # Mostrar resultados finales
                            st.success("✅ Verificación completada exitosamente")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("📱 Procesadas", resultados["procesadas"])
                            with col2:
                                st.metric("✅ Activas", resultados["activas"])
                            with col3:
                                st.metric("⭕ Inactivas", resultados["inactivas"])
                            with col4:
                                st.metric("❌ Errores", resultados["errores"])
                            
                            st.info(f"⏱️ Duración: {resultados['duracion_minutos']:.1f} minutos")
                        
                        except Exception as e:
                            st.error(f"❌ Error durante la verificación: {e}")
    
    except Exception as e:
        st.error(f"❌ Error al cargar lotes: {e}")

# ==================== CONSULTAR RESULTADOS ====================
elif menu_option == "📊 Consultar Resultados":
    st.header("📊 Consultar y Exportar Resultados")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        try:
            response = supabase.table("verificacion_iccids").select("lote").execute()
            lotes = list(set([r['lote'] for r in response.data]))
            lote_filtro = st.selectbox("Filtrar por Lote", ["Todos"] + lotes)
        except:
            lote_filtro = "Todos"
    
    with col2:
        estatus_filtro = st.selectbox(
            "Filtrar por Estado",
            ["Todos", "PENDIENTE", "ACTIVA", "INACTIVA", "ERROR"]
        )
    
    with col3:
        limite_registros = st.number_input(
            "Límite de registros",
            min_value=10,
            max_value=10000,
            value=1000,
            step=100
        )
    
    # Botón de consulta
    if st.button("🔍 Buscar", use_container_width=True):
        try:
            # Construir query
            query = supabase.table("verificacion_iccids").select("*")
            
            if lote_filtro != "Todos":
                query = query.eq("lote", lote_filtro)
            
            if estatus_filtro != "Todos":
                query = query.eq("estatus", estatus_filtro)
            
            query = query.limit(limite_registros)
            
            response = query.execute()
            resultados = response.data
            
            if resultados:
                df = pd.DataFrame(resultados)
                
                st.success(f"✅ Se encontraron {len(df)} registros")
                
                # Mostrar tabla
                st.dataframe(
                    df[[
                        'iccid_completo', 'ultimos_13_digitos', 'estatus',
                        'numero_asignado', 'lote', 'fecha_verificacion', 'observaciones'
                    ]],
                    use_container_width=True,
                    height=400
                )
                
                # Botón de exportación
                st.divider()
                
                # Convertir a Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Resultados')
                
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📥 Descargar Resultados en Excel",
                    data=excel_data,
                    file_name=f"resultados_iccids_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ No se encontraron resultados con los filtros seleccionados")
        
        except Exception as e:
            st.error(f"❌ Error al consultar: {e}")

# ==================== CONFIGURACIÓN ====================
elif menu_option == "⚙️ Configuración":
    st.header("⚙️ Configuración del Sistema")
    
    st.subheader("📊 Información del Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **Configuración Actual:**
        - Velocidad: 3 segundos/ICCID
        - Capacidad: 30,000 ICCIDs/día
        - Timeout: 15 segundos
        - Reintentos: 3 intentos
        """)
    
    with col2:
        st.info("""
        **Base de Datos:**
        - Proveedor: Supabase
        - Plan: Pro
        - Estado: ✅ Conectado
        """)
    
    st.divider()
    
    st.subheader("🗄️ Gestión de Base de Datos")
    
    with st.expander("⚠️ Zona de Peligro - Operaciones Avanzadas"):
        st.warning("Las siguientes operaciones son irreversibles. Úsalas con precaución.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Eliminar Lote Específico", use_container_width=True):
                st.text_input("Nombre del lote a eliminar", key="lote_eliminar")
                if st.button("Confirmar Eliminación"):
                    st.error("Funcionalidad en desarrollo")
        
        with col2:
            if st.button("🔄 Resetear ICCIDs a PENDIENTE", use_container_width=True):
                st.error("Funcionalidad en desarrollo")
    
    st.divider()
    
    st.subheader("📖 Documentación")
    st.markdown("""
    ### Cómo usar el sistema:
    
    1. **Cargar Lote**: Sube un archivo Excel con ICCIDs
    2. **Verificar**: Selecciona el lote y ejecuta la verificación
    3. **Consultar**: Revisa los resultados y exporta a Excel
    
    ### Formatos soportados:
    - ICCID completo: `8952140063719050976F`
    - Solo últimos 13: `0063719050976`
    
    ### Estados posibles:
    - **PENDIENTE**: No verificado aún
    - **ACTIVA**: SIM activa con número asignado
    - **INACTIVA**: SIM requiere activación
    - **ERROR**: Error en la verificación
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>Sistema Verificador de ICCIDs BAIT v1.0 | Desarrollado para procesamiento masivo de hasta 500,000 ICCIDs</p>
</div>
""", unsafe_allow_html=True)
