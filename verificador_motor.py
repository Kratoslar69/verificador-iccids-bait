"""
Motor de Automatización para Verificación de ICCIDs en Portal BAIT
Configurado para procesar 30,000 ICCIDs por día de forma segura y confiable
"""

import os
import time
import re
from datetime import datetime
from typing import Dict, Optional, Tuple
from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PlaywrightTimeout
from tenacity import retry, stop_after_attempt, wait_exponential
from supabase import create_client, Client

class VerificadorICCID:
    """
    Clase principal para verificar ICCIDs en el portal de BAIT
    Configuración: 30,000 verificaciones/día = ~3 segundos por ICCID
    """
    
    def __init__(self, supabase_url=None, supabase_key=None):
        """Inicializar conexión a Supabase y configuración"""
        # Permitir pasar credenciales como parámetros o usar variables de entorno
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_KEY")
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Configuración de velocidad
        self.delay_entre_verificaciones = 3  # 3 segundos entre verificaciones
        self.timeout_pagina = 15000  # 15 segundos timeout
        self.max_reintentos = 3
        
        # URLs
        self.url_portal = "https://mibait.com/haz-tu-portabilidad"
        
        # Estadísticas
        self.stats = {
            "procesadas": 0,
            "activas": 0,
            "inactivas": 0,
            "errores": 0,
            "inicio": None
        }
    
    def extraer_ultimos_13_digitos(self, iccid_completo: str) -> str:
        """
        Extraer los últimos 13 dígitos del ICCID sin la F final
        Ejemplo: 8952140063719050976F -> 0063719050976
        """
        # Limpiar el ICCID de espacios y caracteres no numéricos excepto F
        iccid_limpio = re.sub(r'[^0-9F]', '', iccid_completo.upper())
        
        # Remover el prefijo 895214 si existe
        if iccid_limpio.startswith('895214'):
            iccid_limpio = iccid_limpio[6:]
        
        # Remover la F final si existe
        if iccid_limpio.endswith('F'):
            iccid_limpio = iccid_limpio[:-1]
        
        # Tomar los últimos 13 dígitos
        ultimos_13 = iccid_limpio[-13:] if len(iccid_limpio) >= 13 else iccid_limpio
        
        return ultimos_13
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def verificar_iccid_en_portal(self, page: Page, ultimos_13_digitos: str) -> Tuple[str, Optional[str], str]:
        """
        Verificar una ICCID en el portal de BAIT
        
        Returns:
            Tuple[estatus, numero_asignado, observaciones]
            - estatus: 'ACTIVA', 'INACTIVA', 'ERROR'
            - numero_asignado: número telefónico si está activa, None si no
            - observaciones: mensaje descriptivo
        """
        try:
            # Navegar al portal
            page.goto(self.url_portal, wait_until="domcontentloaded", timeout=self.timeout_pagina)
            time.sleep(2)  # Esperar a que cargue completamente
            
            # Cerrar modal de cookies si aparece
            try:
                boton_cerrar_cookies = page.locator('button:has-text("close"), button:has-text("Aceptar")').first
                if boton_cerrar_cookies.is_visible(timeout=2000):
                    boton_cerrar_cookies.click()
                    time.sleep(0.5)
            except:
                pass  # Si no hay modal de cookies, continuar
            
            # Localizar el campo de ICCID
            # El campo tiene el placeholder "13 dígitos restantes de tu SIM"
            input_iccid = page.locator('input[placeholder*="13 dígitos"]').first
            
            if not input_iccid.is_visible(timeout=5000):
                return "ERROR", None, "Campo de ICCID no encontrado en la página"
            
            # Limpiar y llenar el campo
            input_iccid.click()
            time.sleep(0.3)
            input_iccid.fill("")
            time.sleep(0.3)
            input_iccid.fill(ultimos_13_digitos)
            time.sleep(0.5)
            
            # IMPORTANTE: Presionar Enter para activar la validación
            input_iccid.press("Enter")
            
            # CRÍTICO: Esperar 5 segundos para que el popup aparezca
            # El popup tarda ~3-5 segundos en mostrarse después de presionar Enter
            print(f"[DEBUG] Esperando popup para ICCID {ultimos_13_digitos}...")
            time.sleep(5)  # Espera fija de 5 segundos
            
            max_intentos = 10  # 10 intentos x 0.5 segundos = 5 segundos adicionales
            popup_detectado = False
            estado_final = None
            numero_final = None
            observaciones_final = None
            
            for intento in range(max_intentos):
                time.sleep(0.5)  # Esperar medio segundo entre cada intento
                
                try:
                    # CASO 1: Verificar PRIMERO si aparece el popup de INACTIVA
                    # Buscar en el HTML completo los elementos únicos del popup
                    page_text = page.content()
                    tiene_whatsapp = "btz.mx/whatsappbait" in page_text
                    tiene_necesita = "necesita activarse" in page_text
                    
                    if tiene_whatsapp or tiene_necesita:
                        print(f"[DEBUG] ✓ Popup de INACTIVA detectado en intento {intento+1}")
                        print(f"[DEBUG]   - whatsapp: {tiene_whatsapp}, necesita: {tiene_necesita}")
                        estado_final = "INACTIVA"
                        numero_final = None
                        observaciones_final = "SIM requiere activación"
                        popup_detectado = True
                        break
                    
                    # CASO 2: Si NO es INACTIVA, buscar el campo de validación automática (ACTIVA)
                    # El número aparece en un input con placeholder "Validación automática de tu número Bait"
                    try:
                        campo_validacion = page.locator('input[placeholder*="Validación automática"]').first
                        if campo_validacion.is_visible(timeout=500):
                            numero = campo_validacion.input_value()
                            # Verificar que sea un número de 10 dígitos
                            if numero and len(numero) == 10 and numero.isdigit():
                                print(f"[DEBUG] ✓ Número telefónico encontrado en campo validación: {numero} - ICCID ACTIVA")
                                estado_final = "ACTIVA"
                                numero_final = numero
                                observaciones_final = f"SIM activa con número {numero}"
                                popup_detectado = True
                                break
                    except:
                        pass
                    
                    # Si llegamos al intento 5, 10 y 15, mostrar progreso
                    if (intento + 1) % 5 == 0:
                        print(f"[DEBUG] Intento {intento+1}/{max_intentos} - Esperando popup...")
                        
                except Exception as e:
                    print(f"[DEBUG] Error en intento {intento+1}: {str(e)}")
                    continue
            
            # Verificar si se detectó algo
            if popup_detectado:
                return estado_final, numero_final, observaciones_final
            else:
                print(f"[DEBUG] ⚠ No se detectó popup después de {max_intentos} intentos - Marcando como ERROR")
            
            # Si no se encontró información clara después de esperar
            return "ERROR", None, "No se pudo determinar el estado de la SIM (timeout o respuesta inesperada)"
            
        except PlaywrightTimeout:
            return "ERROR", None, "Timeout al cargar la página"
        except Exception as e:
            return "ERROR", None, f"Error: {str(e)}"
    
    def actualizar_iccid_en_db(self, iccid_completo: str, estatus: str, 
                               numero_asignado: Optional[str], observaciones: str):
        """Actualizar el estado de una ICCID en Supabase"""
        try:
            data = {
                "estatus": estatus,
                "numero_asignado": numero_asignado,
                "fecha_verificacion": datetime.now().isoformat(),
                "observaciones": observaciones
            }
            
            # Actualizar registro existente
            response = self.supabase.table("verificacion_iccids").update(data).eq(
                "iccid_completo", iccid_completo
            ).execute()
            
            return True
        except Exception as e:
            print(f"Error al actualizar DB: {e}")
            return False
    
    def inicializar_proceso(self, lote_nombre: str, total: int):
        """Inicializar o actualizar el registro de proceso en la base de datos"""
        try:
            # Intentar obtener proceso existente
            response = self.supabase.table("proceso_verificacion").select("*").eq(
                "lote", lote_nombre
            ).execute()
            
            if response.data:
                # Actualizar proceso existente
                self.supabase.table("proceso_verificacion").update({
                    "estado": "EJECUTANDO",
                    "progreso_total": total,
                    "fecha_actualizacion": datetime.now().isoformat()
                }).eq("lote", lote_nombre).execute()
            else:
                # Crear nuevo proceso
                self.supabase.table("proceso_verificacion").insert({
                    "lote": lote_nombre,
                    "estado": "EJECUTANDO",
                    "progreso_actual": 0,
                    "progreso_total": total,
                    "activas": 0,
                    "inactivas": 0,
                    "errores": 0
                }).execute()
        except Exception as e:
            print(f"Error al inicializar proceso: {e}")
    
    def actualizar_progreso_proceso(self, lote_nombre: str, progreso: int, 
                                    activas: int, inactivas: int, errores: int):
        """Actualizar el progreso del proceso en la base de datos"""
        try:
            self.supabase.table("proceso_verificacion").update({
                "progreso_actual": progreso,
                "activas": activas,
                "inactivas": inactivas,
                "errores": errores,
                "fecha_actualizacion": datetime.now().isoformat()
            }).eq("lote", lote_nombre).execute()
        except Exception as e:
            print(f"Error al actualizar progreso: {e}")
    
    def obtener_estado_proceso(self, lote_nombre: str) -> str:
        """Obtener el estado actual del proceso desde la base de datos"""
        try:
            response = self.supabase.table("proceso_verificacion").select("estado").eq(
                "lote", lote_nombre
            ).execute()
            
            if response.data:
                return response.data[0]['estado']
            return "DETENIDO"
        except:
            return "DETENIDO"
    
    def finalizar_proceso(self, lote_nombre: str, estado: str = "COMPLETADO"):
        """Marcar el proceso como finalizado"""
        try:
            self.supabase.table("proceso_verificacion").update({
                "estado": estado,
                "fecha_actualizacion": datetime.now().isoformat()
            }).eq("lote", lote_nombre).execute()
        except Exception as e:
            print(f"Error al finalizar proceso: {e}")
    
    def procesar_lote(self, lote_nombre: str, limite: Optional[int] = None, 
                      callback_progreso=None) -> Dict:
        """
        Procesar un lote de ICCIDs pendientes con control de estado
        Procesa automáticamente en bloques de 1000 para superar limitación de Supabase
        
        Args:
            lote_nombre: Nombre del lote a procesar
            limite: Número máximo de ICCIDs a procesar (None = todas)
            callback_progreso: Función callback para reportar progreso
        
        Returns:
            Diccionario con estadísticas del procesamiento
        """
        self.stats = {
            "procesadas": 0,
            "activas": 0,
            "inactivas": 0,
            "errores": 0,
            "inicio": datetime.now()
        }
        
        # Primero, contar el total de ICCIDs pendientes (sin límite)
        count_response = self.supabase.table("verificacion_iccids").select(
            "id", count="exact"
        ).eq("lote", lote_nombre).eq("estatus", "PENDIENTE").execute()
        
        total_pendientes = count_response.count if count_response.count else 0
        
        if total_pendientes == 0:
            return {"error": "No hay ICCIDs pendientes en este lote"}
        
        # Determinar cuántas ICCIDs procesar
        total_a_procesar = min(limite, total_pendientes) if limite else total_pendientes
        
        print(f"\n🚀 Iniciando verificación de {total_a_procesar:,} ICCIDs del lote '{lote_nombre}'")
        print(f"📄 Total pendientes en lote: {total_pendientes:,}")
        print(f"⏱️  Tiempo estimado: {(total_a_procesar * self.delay_entre_verificaciones) / 60:.1f} minutos")
        print(f"📊 Procesamiento en bloques de 1000 ICCIDs\n")
        
        # Inicializar proceso en la base de datos
        self.inicializar_proceso(lote_nombre, total_a_procesar)
        
        # Iniciar navegador
        with sync_playwright() as p:
            browser: Browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page: Page = context.new_page()
            
            try:
                # Procesar en bloques de 1000 ICCIDs
                bloque_size = 1000
                procesadas_global = 0
                
                while procesadas_global < total_a_procesar:
                    # Verificar estado del proceso antes de consultar siguiente bloque
                    estado_proceso = self.obtener_estado_proceso(lote_nombre)
                    if estado_proceso == "DETENIDO":
                        print("\n⏹️  Proceso detenido por el usuario")
                        self.finalizar_proceso(lote_nombre, "DETENIDO")
                        break
                    
                    # Calcular cuántas ICCIDs quedan por procesar
                    restantes = total_a_procesar - procesadas_global
                    limite_bloque = min(bloque_size, restantes)
                    
                    print(f"\n📦 Consultando bloque: {procesadas_global + 1} a {procesadas_global + limite_bloque}")
                    
                    # Obtener siguiente bloque de ICCIDs pendientes
                    query = self.supabase.table("verificacion_iccids").select("*").eq(
                        "lote", lote_nombre
                    ).eq("estatus", "PENDIENTE").limit(limite_bloque)
                    
                    response = query.execute()
                    iccids_bloque = response.data
                    
                    if not iccids_bloque:
                        # Verificar si realmente no hay más ICCIDs pendientes
                        print("\n⚠️ Bloque vacío. Verificando si quedan ICCIDs pendientes...")
                        
                        # Contar ICCIDs pendientes reales
                        count_check = self.supabase.table("verificacion_iccids").select(
                            "id", count="exact"
                        ).eq("lote", lote_nombre).eq("estatus", "PENDIENTE").execute()
                        
                        pendientes_reales = count_check.count if count_check.count else 0
                        
                        print(f"📄 ICCIDs pendientes en BD: {pendientes_reales}")
                        
                        if pendientes_reales > 0:
                            print(f"⚠️ Hay {pendientes_reales} ICCIDs pendientes pero el bloque está vacío. Reintentando en 5s...")
                            time.sleep(5)
                            continue  # Reintentar consulta
                        else:
                            print("\n✅ Confirmado: No hay más ICCIDs pendientes")
                            break
                    
                    print(f"✅ Bloque obtenido: {len(iccids_bloque)} ICCIDs")
                    
                    # Procesar cada ICCID del bloque
                    for idx_bloque, registro in enumerate(iccids_bloque, 1):
                        # Verificar estado del proceso antes de continuar
                        estado_proceso = self.obtener_estado_proceso(lote_nombre)
                        
                        if estado_proceso == "DETENIDO":
                            print("\n⏹️  Proceso detenido por el usuario")
                            self.finalizar_proceso(lote_nombre, "DETENIDO")
                            break
                        
                        # Si está pausado, esperar hasta que se reanude o detenga
                        while estado_proceso == "PAUSADO":
                            print(f"\n⏸️  Proceso pausado. Esperando...")
                            time.sleep(2)
                            estado_proceso = self.obtener_estado_proceso(lote_nombre)
                            if estado_proceso == "DETENIDO":
                                print("\n⏹️  Proceso detenido por el usuario")
                                self.finalizar_proceso(lote_nombre, "DETENIDO")
                                return self.stats
                        
                        # Calcular índice global
                        idx_global = procesadas_global + idx_bloque
                        
                        iccid_completo = registro['iccid_completo']
                        ultimos_13 = registro['ultimos_13_digitos']
                        
                        print(f"[{idx_global}/{total_a_procesar}] Verificando ICCID: {iccid_completo}")
                        
                        # Verificar en el portal
                        estatus, numero, observaciones = self.verificar_iccid_en_portal(
                            page, ultimos_13
                        )
                        
                        # Actualizar en base de datos
                        self.actualizar_iccid_en_db(
                            iccid_completo, estatus, numero, observaciones
                        )
                        
                        # Actualizar estadísticas
                        self.stats["procesadas"] += 1
                        if estatus == "ACTIVA":
                            self.stats["activas"] += 1
                        elif estatus == "INACTIVA":
                            self.stats["inactivas"] += 1
                        else:
                            self.stats["errores"] += 1
                        
                        print(f"   ✓ Estado: {estatus} | {observaciones}")
                        
                        # Actualizar progreso en la base de datos
                        self.actualizar_progreso_proceso(
                            lote_nombre, idx_global, 
                            self.stats["activas"], 
                            self.stats["inactivas"], 
                            self.stats["errores"]
                        )
                        
                        # Callback de progreso
                        if callback_progreso:
                            callback_progreso(idx_global, total_a_procesar, estatus, numero)
                        
                        # Delay entre verificaciones
                        time.sleep(self.delay_entre_verificaciones)
                    
                    # Actualizar contador global
                    procesadas_global += len(iccids_bloque)
                    
                    print(f"\n✅ Bloque completado. Progreso total: {procesadas_global}/{total_a_procesar}\n")
                    
                    # Si se detuvo el proceso, salir del while
                    if estado_proceso == "DETENIDO":
                        break
            
            finally:
                browser.close()
        
        # Calcular estadísticas finales
        duracion = (datetime.now() - self.stats["inicio"]).total_seconds() / 60
        
        self.stats["duracion_minutos"] = duracion
        
        # Verificar si realmente se completaron todas las ICCIDs solicitadas
        count_final = self.supabase.table("verificacion_iccids").select(
            "id", count="exact"
        ).eq("lote", lote_nombre).eq("estatus", "PENDIENTE").execute()
        
        pendientes_finales = count_final.count if count_final.count else 0
        
        if pendientes_finales > 0:
            print(f"\n⚠️ ADVERTENCIA: Aún quedan {pendientes_finales} ICCIDs pendientes")
            print(f"📊 Procesadas: {self.stats['procesadas']} de {total_a_procesar} solicitadas")
            self.finalizar_proceso(lote_nombre, "INCOMPLETO")
        else:
            # Marcar proceso como completado
            self.finalizar_proceso(lote_nombre, "COMPLETADO")
        
        print(f"\n{'='*60}")
        print(f"✅ Verificación completada")
        print(f"📊 Procesadas: {self.stats['procesadas']}")
        print(f"✅ Activas: {self.stats['activas']}")
        print(f"⭕ Inactivas: {self.stats['inactivas']}")
        print(f"❌ Errores: {self.stats['errores']}")
        print(f"⏱️  Duración: {duracion:.1f} minutos")
        print(f"{'='*60}\n")
        
        return self.stats
    def obtener_estadisticas_lote(self, lote_nombre: str) -> Dict:
        """Obtener estadísticas de un lote"""
        try:
            response = self.supabase.table("verificacion_iccids").select(
                "estatus"
            ).eq("lote", lote_nombre).execute()
            
            registros = response.data
            total = len(registros)
            
            stats = {
                "total": total,
                "pendientes": sum(1 for r in registros if r['estatus'] == 'PENDIENTE'),
                "activas": sum(1 for r in registros if r['estatus'] == 'ACTIVA'),
                "inactivas": sum(1 for r in registros if r['estatus'] == 'INACTIVA'),
                "errores": sum(1 for r in registros if r['estatus'] == 'ERROR')
            }
            
            return stats
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    # Prueba básica
    verificador = VerificadorICCID()
    print("✓ Verificador inicializado correctamente")
    print(f"✓ Configuración: {verificador.delay_entre_verificaciones}s entre verificaciones")
    print(f"✓ Capacidad: ~{86400 // verificador.delay_entre_verificaciones} ICCIDs/día")
