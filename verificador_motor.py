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
            
            # Esperar a que aparezca el popup de respuesta (hasta 10 segundos)
            time.sleep(2)
            
            # CASO 1: Verificar si aparece el modal de "necesita activarse" (INACTIVA)
            try:
                # Buscar el texto "necesita activarse" en todo el contenido de la página
                page_text = page.content()
                print(f"[DEBUG] Buscando popup para ICCID {ultimos_13_digitos}...")
                
                if "necesita activarse" in page_text:
                    print(f"[DEBUG] ✓ Encontrado 'necesita activarse' - ICCID INACTIVA")
                    return "INACTIVA", None, "SIM requiere activación"
                else:
                    print(f"[DEBUG] ✗ No se encontró 'necesita activarse'")
            except Exception as e:
                print(f"[DEBUG] Error en CASO 1: {str(e)}")
                pass
            
            # CASO 2: Verificar si aparece el modal con "Validación automática" y un número (ACTIVA)
            try:
                # Buscar el modal que contiene "Validación automática de tu número Bait"
                page_text = page.content()
                print(f"[DEBUG] Buscando 'Validación automática'...")
                
                if "Validación automática" in page_text and "necesita activarse" not in page_text:
                    print(f"[DEBUG] ✓ Encontrado 'Validación automática' - Buscando número...")
                    # Buscar número telefónico de 10 dígitos
                    numeros_encontrados = re.findall(r'\b[0-9]{10}\b', page_text)
                    # Filtrar números que no sean ICCID ni el prefijo
                    numeros_validos = [n for n in numeros_encontrados if not n.startswith('895214') and n != ultimos_13_digitos[:10]]
                    if numeros_validos:
                        numero = numeros_validos[0]
                        print(f"[DEBUG] ✓ Número encontrado: {numero} - ICCID ACTIVA")
                        return "ACTIVA", numero, f"SIM activa con número {numero}"
                    else:
                        print(f"[DEBUG] ✗ No se encontró número válido")
                else:
                    print(f"[DEBUG] ✗ No se encontró 'Validación automática'")
            except Exception as e:
                print(f"[DEBUG] Error en CASO 2: {str(e)}")
                pass
            
            # CASO 3: Si no se detectó ni "necesita activarse" ni "Validación automática", es un ERROR
            print(f"[DEBUG] ⚠ No se pudo determinar el estado - Marcando como ERROR")
            # No buscar números en toda la página para evitar falsos positivos
            
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
    
    def procesar_lote(self, lote_nombre: str, limite: Optional[int] = None, 
                      callback_progreso=None) -> Dict:
        """
        Procesar un lote de ICCIDs pendientes
        
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
        
        # Obtener ICCIDs pendientes del lote
        query = self.supabase.table("verificacion_iccids").select("*").eq(
            "lote", lote_nombre
        ).eq("estatus", "PENDIENTE")
        
        if limite:
            query = query.limit(limite)
        
        response = query.execute()
        iccids_pendientes = response.data
        
        if not iccids_pendientes:
            return {"error": "No hay ICCIDs pendientes en este lote"}
        
        total = len(iccids_pendientes)
        print(f"\n🚀 Iniciando verificación de {total} ICCIDs del lote '{lote_nombre}'")
        print(f"⏱️  Tiempo estimado: {(total * self.delay_entre_verificaciones) / 60:.1f} minutos")
        print(f"📊 Objetivo: 30,000 ICCIDs/día\n")
        
        # Iniciar navegador
        with sync_playwright() as p:
            browser: Browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page: Page = context.new_page()
            
            try:
                for idx, registro in enumerate(iccids_pendientes, 1):
                    iccid_completo = registro['iccid_completo']
                    ultimos_13 = registro['ultimos_13_digitos']
                    
                    print(f"[{idx}/{total}] Verificando ICCID: {iccid_completo}")
                    
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
                    
                    # Callback de progreso
                    if callback_progreso:
                        callback_progreso(idx, total, estatus, numero)
                    
                    # Delay entre verificaciones
                    if idx < total:
                        time.sleep(self.delay_entre_verificaciones)
                
            finally:
                browser.close()
        
        # Calcular estadísticas finales
        self.stats["fin"] = datetime.now()
        self.stats["duracion_minutos"] = (
            self.stats["fin"] - self.stats["inicio"]
        ).total_seconds() / 60
        
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
