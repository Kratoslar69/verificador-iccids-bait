#!/usr/bin/env python3.11
"""
Worker Daemon Independiente para Verificación de ICCIDs
Este proceso corre 24/7 independiente de Streamlit
"""

import os
import sys
import time
import logging
from datetime import datetime
from verificador_motor import VerificadorICCID

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/worker_daemon.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class WorkerDaemon:
    """Worker daemon que procesa ICCIDs de forma continua"""
    
    def __init__(self):
        # Obtener credenciales de Supabase
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logger.error("❌ Faltan credenciales de Supabase")
            sys.exit(1)
        
        # Obtener lote asignado (opcional)
        self.lote_asignado = os.getenv("LOTE_ASIGNADO")
        
        if self.lote_asignado:
            logger.info(f"📌 Lote asignado a esta instancia: {self.lote_asignado}")
        else:
            logger.info("📌 Sin lote asignado - procesará todos los lotes disponibles")
        
        self.verificador = VerificadorICCID(self.supabase_url, self.supabase_key)
        self.proceso_actual = None
        
        logger.info("✅ Worker Daemon inicializado correctamente")
    
    def buscar_procesos_pendientes(self):
        """Buscar procesos con estado EJECUTANDO en la base de datos"""
        try:
            query = self.verificador.supabase.table("proceso_verificacion").select("*").eq(
                "estado", "EJECUTANDO"
            )
            
            # Si hay un lote asignado, filtrar solo ese lote
            if self.lote_asignado:
                query = query.eq("lote", self.lote_asignado)
            
            response = query.execute()
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"❌ Error al buscar procesos: {e}")
            return []
    
    def procesar_lote(self, lote_nombre: str):
        """Procesar un lote de ICCIDs"""
        try:
            logger.info(f"🚀 Iniciando procesamiento de lote: {lote_nombre}")
            
            # Obtener información del proceso
            response = self.verificador.supabase.table("proceso_verificacion").select("*").eq(
                "lote", lote_nombre
            ).execute()
            
            if not response.data:
                logger.warning(f"⚠️ No se encontró proceso para lote: {lote_nombre}")
                return
            
            proceso = response.data[0]
            progreso_actual = proceso['progreso_actual']
            progreso_total = proceso['progreso_total']
            
            # Calcular cuántas ICCIDs quedan por procesar
            restantes = progreso_total - progreso_actual
            
            logger.info(f"📊 Progreso: {progreso_actual}/{progreso_total} ({restantes} restantes)")
            
            # Ejecutar verificación (sin límite para procesar todas las pendientes)
            resultados = self.verificador.procesar_lote(
                lote_nombre=lote_nombre,
                limite=None,  # Sin límite, procesar todas
                callback_progreso=None
            )
            
            logger.info(f"✅ Lote completado: {lote_nombre}")
            logger.info(f"📊 Resultados: {resultados}")
            
        except Exception as e:
            logger.error(f"❌ Error al procesar lote {lote_nombre}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Marcar como error en la base de datos
            try:
                self.verificador.finalizar_proceso(lote_nombre, "ERROR")
            except:
                pass
    
    def run(self):
        """Loop principal del daemon"""
        logger.info("🔄 Worker Daemon iniciado - Esperando procesos...")
        
        intervalo_revision = 10  # Revisar cada 10 segundos
        
        while True:
            try:
                # Buscar procesos pendientes
                procesos = self.buscar_procesos_pendientes()
                
                if procesos:
                    logger.info(f"📦 Encontrados {len(procesos)} proceso(s) pendiente(s)")
                    
                    for proceso in procesos:
                        lote_nombre = proceso['lote']
                        
                        # Verificar si ya estamos procesando este lote
                        if self.proceso_actual == lote_nombre:
                            logger.info(f"⏳ Ya procesando lote: {lote_nombre}")
                            continue
                        
                        # Marcar como proceso actual
                        self.proceso_actual = lote_nombre
                        
                        # Procesar lote
                        self.procesar_lote(lote_nombre)
                        
                        # Limpiar proceso actual
                        self.proceso_actual = None
                else:
                    logger.info("💤 No hay procesos pendientes")
                
                # Esperar antes de la siguiente revisión
                time.sleep(intervalo_revision)
                
            except KeyboardInterrupt:
                logger.info("⏹️ Worker Daemon detenido por usuario")
                break
            except Exception as e:
                logger.error(f"❌ Error en loop principal: {e}")
                import traceback
                logger.error(traceback.format_exc())
                
                # Esperar antes de reintentar
                time.sleep(30)


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("🚀 Iniciando Worker Daemon para Verificación de ICCIDs")
    logger.info("="*60)
    
    daemon = WorkerDaemon()
    daemon.run()
