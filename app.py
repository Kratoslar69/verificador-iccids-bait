"""
Sistema Verificador de ICCIDs BAIT - Interfaz Web
Aplicación Streamlit para gestionar verificaciones de hasta 500,000 ICCIDs
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO
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

# Inicializar Supabase
@st.cache_resource
def init_supabase():
    # Intentar cargar desde Streamlit secrets primero, luego desde variables de entorno
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_SERVICE_KEY"]
    except:
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
                        # Validar duplicados en el archivo Excel
                        duplicados_en_archivo = df['ICCID'].duplicated().sum()
                        if duplicados_en_archivo > 0:
                            st.warning(f"⚠️ Se encontraron {duplicados_en_archivo} ICCIDs duplicadas en el archivo")
                        
                        # Verificar si el lote ya existe en la base de datos
                        response_lote = supabase.table("verificacion_iccids").select("lote").eq(
                            "lote", nombre_lote
                        ).limit(1).execute()
                        
                        if response_lote.data:
                            st.warning(f"⚠️ El lote '{nombre_lote}' ya existe en la base de datos")
                            accion_duplicados = st.radio(
                                "¿Qué deseas hacer?",
                                ["Cancelar carga", "Agregar ICCIDs al lote existente", "Sobrescribir lote completo"],
                                key="radio_duplicados"
                            )
                            
                            if accion_duplicados == "Cancelar carga":
                                st.info("ℹ️ Carga cancelada")
                                st.stop()
                            elif accion_duplicados == "Sobrescribir lote completo":
                                # Eliminar lote existente
                                supabase.table("verificacion_iccids").delete().eq(
                                    "lote", nombre_lote
                                ).execute()
                                st.info(f"🗑️ Lote '{nombre_lote}' eliminado. Procediendo con la carga...")
                        
                        # Procesar ICCIDs
                        try:
                            supabase_url = st.secrets["SUPABASE_URL"]
                            supabase_key = st.secrets["SUPABASE_SERVICE_KEY"]
                        except:
                            supabase_url = os.getenv("SUPABASE_URL")
                            supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
                        verificador = VerificadorICCID(supabase_url, supabase_key)
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
    
    # Verificar si hay procesos en ejecución
    try:
        response_procesos = supabase.table("proceso_verificacion").select("*").in_(
            "estado", ["EJECUTANDO", "PAUSADO"]
        ).execute()
        procesos_activos = response_procesos.data
        
        if procesos_activos:
            st.info(f"🔄 Hay {len(procesos_activos)} proceso(s) activo(s) - Auto-actualización cada 5 segundos")
            
            # Auto-refresh cada 5 segundos si hay procesos activos
            import streamlit as st
            st.markdown(
                """
                <script>
                setTimeout(function(){
                    window.location.reload();
                }, 5000);
                </script>
                """,
                unsafe_allow_html=True
            )
            
            for proceso in procesos_activos:
                # Calcular tiempo transcurrido
                from datetime import datetime
                fecha_inicio = datetime.fromisoformat(proceso['fecha_inicio'].replace('Z', '+00:00'))
                tiempo_transcurrido = datetime.now(fecha_inicio.tzinfo) - fecha_inicio
                horas = int(tiempo_transcurrido.total_seconds() // 3600)
                minutos = int((tiempo_transcurrido.total_seconds() % 3600) // 60)
                segundos = int(tiempo_transcurrido.total_seconds() % 60)
                tiempo_str = f"{horas}h {minutos}m {segundos}s"
                
                # Calcular porcentaje
                porcentaje = (proceso['progreso_actual'] / proceso['progreso_total'] * 100) if proceso['progreso_total'] > 0 else 0
                
                with st.expander(f"📦 Lote: {proceso['lote']} - {proceso['estado']} - {porcentaje:.1f}%", expanded=True):
                    # Primera fila: Tiempo y progreso
                    col_time1, col_time2 = st.columns(2)
                    with col_time1:
                        st.metric("⏱️ Tiempo Corriendo", tiempo_str)
                    with col_time2:
                        st.metric("📈 Progreso", f"{proceso['progreso_actual']:,}/{proceso['progreso_total']:,}")
                    
                    # Barra de progreso
                    st.progress(porcentaje / 100)
                    
                    # Segunda fila: Estadísticas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("✅ Activas", f"{proceso['activas']:,}")
                    with col2:
                        st.metric("⭕ Inactivas", f"{proceso['inactivas']:,}")
                    with col3:
                        st.metric("❌ Errores", f"{proceso['errores']:,}")
                    
                    # Botones de control
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    
                    with col_btn1:
                        if proceso['estado'] == "EJECUTANDO":
                            if st.button("⏸️ Pausar", key=f"pausar_{proceso['lote']}"):
                                supabase.table("proceso_verificacion").update({
                                    "estado": "PAUSADO"
                                }).eq("lote", proceso['lote']).execute()
                                st.success("⏸️ Proceso pausado")
                                st.rerun()
                        else:
                            if st.button("▶️ Reanudar", key=f"reanudar_{proceso['lote']}"):
                                supabase.table("proceso_verificacion").update({
                                    "estado": "EJECUTANDO"
                                }).eq("lote", proceso['lote']).execute()
                                st.success("▶️ Proceso reanudado")
                                st.rerun()
                    
                    with col_btn2:
                        if st.button("⏹️ Detener", key=f"detener_{proceso['lote']}", type="primary"):
                            supabase.table("proceso_verificacion").update({
                                "estado": "DETENIDO"
                            }).eq("lote", proceso['lote']).execute()
                            st.warning("⏹️ Proceso detenido")
                            st.rerun()
                    
                    with col_btn3:
                        if st.button("🔄 Actualizar", key=f"actualizar_{proceso['lote']}"):
                            st.rerun()
            
            st.divider()
    except Exception as e:
        st.error(f"❌ Error al verificar procesos: {e}")
    
    # Obtener lotes disponibles
    try:
        # Usar RPC para obtener lotes únicos directamente (evita límite de 1000 registros)
        response = supabase.rpc('get_lotes_unicos').execute()
        
        if response.data and len(response.data) > 0:
            lotes_disponibles = sorted([item['lote'] for item in response.data])
        else:
            # Fallback: obtener con paginación si RPC no existe
            all_data = []
            offset = 0
            limit = 1000
            while True:
                response = supabase.table("verificacion_iccids").select("lote").range(offset, offset + limit - 1).execute()
                if not response.data:
                    break
                all_data.extend(response.data)
                if len(response.data) < limit:
                    break
                offset += limit
            
            if not all_data:
                st.warning("⚠️ No hay lotes disponibles. Primero carga un lote de ICCIDs.")
                lotes_disponibles = []
            else:
                lotes_disponibles = sorted(list(set([r['lote'] for r in all_data])))
        
        if lotes_disponibles:
            
            # Formulario de verificación
            with st.form("form_verificar"):
                lote_seleccionado = st.selectbox(
                    "Selecciona el lote a verificar",
                    options=lotes_disponibles
                )
                
                # Mostrar estadísticas del lote
                if lote_seleccionado:
                    # Obtener estadísticas del lote seleccionado
                    response_stats = supabase.table("verificacion_iccids").select("estatus").eq("lote", lote_seleccionado).execute()
                    if response_stats.data:
                        lote_df = pd.DataFrame(response_stats.data)
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
                        # Marcar proceso como EJECUTANDO en la base de datos
                        # El worker daemon lo detectará y comenzará a procesarlo
                        try:
                            # Verificar si ya hay un proceso activo para este lote
                            response_check = supabase.table("proceso_verificacion").select("*").eq(
                                "lote", lote_seleccionado
                            ).in_("estado", ["EJECUTANDO", "PAUSADO"]).execute()
                            
                            if response_check.data:
                                st.warning("⚠️ Ya hay un proceso activo para este lote")
                            else:
                                # Crear o actualizar proceso como EJECUTANDO
                                response_exists = supabase.table("proceso_verificacion").select("*").eq(
                                    "lote", lote_seleccionado
                                ).execute()
                                
                                total_pendientes = pendientes if limite_verificacion == 0 else min(limite_verificacion, pendientes)
                                
                                if response_exists.data:
                                    # Actualizar proceso existente
                                    supabase.table("proceso_verificacion").update({
                                        "estado": "EJECUTANDO",
                                        "progreso_total": total_pendientes,
                                        "fecha_inicio": datetime.now().isoformat(),
                                        "fecha_actualizacion": datetime.now().isoformat()
                                    }).eq("lote", lote_seleccionado).execute()
                                else:
                                    # Crear nuevo proceso
                                    supabase.table("proceso_verificacion").insert({
                                        "lote": lote_seleccionado,
                                        "estado": "EJECUTANDO",
                                        "progreso_actual": 0,
                                        "progreso_total": total_pendientes,
                                        "activas": 0,
                                        "inactivas": 0,
                                        "errores": 0
                                    }).execute()
                                
                                st.success("✅ Proceso iniciado en background")
                                st.info("🔄 El worker daemon detectará el proceso y comenzará a procesarlo")
                                st.info("🔒 El proceso continuará aunque reinicies Streamlit o Railway")
                                st.info("📊 Puedes ver el progreso en la sección superior")
                                time.sleep(2)
                                st.rerun()
                        
                        except Exception as e:
                            st.error(f"❌ Error al iniciar verificación: {e}")
                            import traceback
                            st.code(traceback.format_exc())
    
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
    
    # Mostrar estadísticas de lotes
    try:
        response = supabase.table("verificacion_iccids").select("lote, estatus").execute()
        if response.data:
            df_lotes = pd.DataFrame(response.data)
            lotes_stats = df_lotes.groupby('lote')['estatus'].value_counts().unstack(fill_value=0)
            
            st.subheader("📊 Estadísticas por Lote")
            st.dataframe(lotes_stats, use_container_width=True)
            
            # Calcular totales
            lotes_stats['TOTAL'] = lotes_stats.sum(axis=1)
            
            st.divider()
    except Exception as e:
        st.error(f"❌ Error al cargar estadísticas: {e}")
    
    # Operaciones de limpieza
    with st.expander("🧹 Limpieza de Duplicados"):
        st.info("Buscar y eliminar registros duplicados en la base de datos")
        
        if st.button("🔍 Buscar Duplicados", use_container_width=True):
            try:
                # Buscar duplicados por iccid_completo
                response = supabase.table("verificacion_iccids").select("iccid_completo").execute()
                if response.data:
                    df_check = pd.DataFrame(response.data)
                    duplicados = df_check[df_check.duplicated(subset=['iccid_completo'], keep=False)]
                    
                    if len(duplicados) > 0:
                        st.warning(f"⚠️ Se encontraron {len(duplicados)} registros duplicados")
                        st.dataframe(duplicados.head(20), use_container_width=True)
                        
                        if st.button("🗑️ Eliminar Duplicados (mantener el más reciente)"):
                            st.error("⚠️ Esta operación requiere confirmación manual en la base de datos")
                    else:
                        st.success("✅ No se encontraron duplicados")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    # Eliminar lote específico
    with st.expander("🗑️ Eliminar Lote Completo"):
        st.warning("⚠️ Esta operación eliminará permanentemente todos los registros del lote seleccionado")
        
        try:
            response = supabase.table("verificacion_iccids").select("lote").execute()
            if response.data:
                df_lotes_list = pd.DataFrame(response.data)
                lotes_disponibles = df_lotes_list['lote'].unique().tolist()
                
                lote_a_eliminar = st.selectbox(
                    "Selecciona el lote a eliminar",
                    options=lotes_disponibles,
                    key="select_lote_eliminar"
                )
                
                if lote_a_eliminar:
                    # Mostrar estadísticas del lote
                    lote_data = df_lotes_list[df_lotes_list['lote'] == lote_a_eliminar]
                    st.info(f"📄 Total de registros en '{lote_a_eliminar}': {len(lote_data)}")
                    
                    confirmar = st.text_input(
                        f"Escribe '{lote_a_eliminar}' para confirmar la eliminación",
                        key="confirmar_eliminar"
                    )
                    
                    if st.button("🗑️ ELIMINAR LOTE", type="primary", use_container_width=True):
                        if confirmar == lote_a_eliminar:
                            try:
                                # Eliminar registros del lote
                                supabase.table("verificacion_iccids").delete().eq(
                                    "lote", lote_a_eliminar
                                ).execute()
                                
                                # Eliminar proceso asociado
                                supabase.table("proceso_verificacion").delete().eq(
                                    "lote", lote_a_eliminar
                                ).execute()
                                
                                st.success(f"✅ Lote '{lote_a_eliminar}' eliminado exitosamente")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error al eliminar: {e}")
                        else:
                            st.error("❌ El nombre del lote no coincide")
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    # Resetear ICCIDs a PENDIENTE
    with st.expander("🔄 Resetear ICCIDs a PENDIENTE"):
        st.info("Cambiar el estado de ICCIDs de un lote a PENDIENTE para re-verificarlas")
        
        try:
            response = supabase.table("verificacion_iccids").select("lote").execute()
            if response.data:
                df_lotes_reset = pd.DataFrame(response.data)
                lotes_disponibles_reset = df_lotes_reset['lote'].unique().tolist()
                
                lote_a_resetear = st.selectbox(
                    "Selecciona el lote a resetear",
                    options=lotes_disponibles_reset,
                    key="select_lote_resetear"
                )
                
                estado_a_resetear = st.selectbox(
                    "Resetear ICCIDs con estado:",
                    options=["Todos", "ACTIVA", "INACTIVA", "ERROR"],
                    key="estado_resetear"
                )
                
                if st.button("🔄 Resetear a PENDIENTE", use_container_width=True):
                    try:
                        query = supabase.table("verificacion_iccids").update({
                            "estatus": "PENDIENTE",
                            "numero_asignado": None,
                            "fecha_verificacion": None,
                            "observaciones": "Reseteado manualmente"
                        }).eq("lote", lote_a_resetear)
                        
                        if estado_a_resetear != "Todos":
                            query = query.eq("estatus", estado_a_resetear)
                        
                        response = query.execute()
                        st.success(f"✅ ICCIDs reseteadas exitosamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al resetear: {e}")
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
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
