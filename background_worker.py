"""
Worker en background para procesar ICCIDs de forma asíncrona
Permite que el proceso continúe aunque el usuario cierre el navegador
"""

import threading
import time
import logging
from typing import Dict, Optional
from verificador_motor import VerificadorICCID
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Diccionario global para mantener threads activos
active_threads: Dict[str, threading.Thread] = {}


class BackgroundWorker:
    """Worker para ejecutar verificaciones en background"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.verificador = VerificadorICCID(supabase_url, supabase_key)
    
    def ejecutar_verificacion(self, lote_nombre: str, limite: Optional[int] = None):
        """
        Ejecutar verificación de un lote en background
        Esta función se ejecuta en un thread separado
        """
        try:
            logger.info(f"🚀 Iniciando verificación en background para lote: {lote_nombre}")
            
            # Ejecutar verificación
            resultados = self.verificador.procesar_lote(
                lote_nombre=lote_nombre,
                limite=limite,
                callback_progreso=None  # No usar callback en background
            )
            
            logger.info(f"✅ Verificación completada para lote: {lote_nombre}")
            logger.info(f"📊 Resultados: {resultados}")
            
            # Remover thread de la lista de activos
            if lote_nombre in active_threads:
                del active_threads[lote_nombre]
            
            return resultados
            
        except Exception as e:
            logger.error(f"❌ Error en verificación de lote {lote_nombre}: {e}")
            
            # Marcar proceso como error en la base de datos
            try:
                self.verificador.finalizar_proceso(lote_nombre, "ERROR")
            except:
                pass
            
            # Remover thread de la lista de activos
            if lote_nombre in active_threads:
                del active_threads[lote_nombre]
            
            raise


def iniciar_verificacion_background(lote_nombre: str, limite: Optional[int] = None,
                                    supabase_url: str = None, supabase_key: str = None) -> bool:
    """
    Iniciar verificación de un lote en background
    
    Args:
        lote_nombre: Nombre del lote a procesar
        limite: Límite de ICCIDs a procesar (None = todas)
        supabase_url: URL de Supabase
        supabase_key: Key de Supabase
    
    Returns:
        True si se inició correctamente, False si ya hay un proceso activo
    """
    # Verificar si ya hay un thread activo para este lote
    if lote_nombre in active_threads and active_threads[lote_nombre].is_alive():
        logger.warning(f"⚠️ Ya hay un proceso activo para el lote: {lote_nombre}")
        return False
    
    # Obtener credenciales de Supabase
    if not supabase_url or not supabase_key:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    # Crear worker
    worker = BackgroundWorker(supabase_url, supabase_key)
    
    # Crear y lanzar thread
    thread = threading.Thread(
        target=worker.ejecutar_verificacion,
        args=(lote_nombre, limite),
        daemon=True,  # Thread daemon para que no bloquee el cierre del programa
        name=f"Worker-{lote_nombre}"
    )
    
    # Guardar referencia al thread
    active_threads[lote_nombre] = thread
    
    # Iniciar thread
    thread.start()
    
    logger.info(f"✅ Proceso en background iniciado para lote: {lote_nombre}")
    logger.info(f"🔢 Threads activos: {len(active_threads)}")
    
    return True


def obtener_threads_activos() -> Dict[str, bool]:
    """
    Obtener lista de threads activos
    
    Returns:
        Diccionario con nombre de lote y estado (True = activo)
    """
    return {
        lote: thread.is_alive() 
        for lote, thread in active_threads.items()
    }


def detener_verificacion_background(lote_nombre: str, supabase_url: str = None, 
                                    supabase_key: str = None) -> bool:
    """
    Detener verificación en background marcando el proceso como DETENIDO
    El thread verificará el estado y se detendrá en la siguiente iteración
    
    Args:
        lote_nombre: Nombre del lote a detener
        supabase_url: URL de Supabase
        supabase_key: Key de Supabase
    
    Returns:
        True si se marcó como detenido correctamente
    """
    try:
        # Obtener credenciales
        if not supabase_url or not supabase_key:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        # Crear verificador para actualizar estado
        verificador = VerificadorICCID(supabase_url, supabase_key)
        
        # Marcar como detenido en la base de datos
        verificador.supabase.table("proceso_verificacion").update({
            "estado": "DETENIDO"
        }).eq("lote", lote_nombre).execute()
        
        logger.info(f"⏹️ Proceso marcado como DETENIDO: {lote_nombre}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error al detener proceso {lote_nombre}: {e}")
        return False


if __name__ == "__main__":
    # Prueba básica
    print("✓ Módulo de background worker cargado correctamente")
    print(f"✓ Threads activos: {len(active_threads)}")
