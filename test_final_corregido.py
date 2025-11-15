"""
Prueba final con el código corregido - detectar campo input
"""

import time
from playwright.sync_api import sync_playwright

def test_iccid(iccid_13_digitos, nombre, esperado):
    """Probar una ICCID con el código corregido"""
    
    url = "https://mibait.com/haz-tu-portabilidad"
    
    print(f"\n{'='*60}")
    print(f"PRUEBA: {nombre}")
    print(f"ICCID: {iccid_13_digitos}")
    print(f"Esperado: {esperado}")
    print(f"{'='*60}\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        
        try:
            # Navegar
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
            
            # Llenar campo
            input_iccid = page.locator('input[placeholder*="13 dígitos"]').first
            input_iccid.click()
            time.sleep(0.3)
            input_iccid.fill(iccid_13_digitos)
            time.sleep(0.5)
            input_iccid.press("Enter")
            
            # Esperar 5 segundos
            print("[DEBUG] Esperando 5 segundos...")
            time.sleep(5)
            
            # Verificar contenido
            max_intentos = 10
            resultado = None
            
            for intento in range(max_intentos):
                time.sleep(0.5)
                
                try:
                    # CASO 1: Verificar popup INACTIVA
                    page_text = page.content()
                    tiene_whatsapp = "btz.mx/whatsappbait" in page_text
                    tiene_necesita = "necesita activarse" in page_text
                    
                    if tiene_whatsapp or tiene_necesita:
                        print(f"[DEBUG] ✓ Popup INACTIVA detectado en intento {intento+1}")
                        resultado = "INACTIVA"
                        break
                    
                    # CASO 2: Verificar campo de validación automática (ACTIVA)
                    try:
                        campo_validacion = page.locator('input[placeholder*="Validación automática"]').first
                        if campo_validacion.is_visible(timeout=500):
                            numero = campo_validacion.input_value()
                            if numero and len(numero) == 10 and numero.isdigit():
                                print(f"[DEBUG] ✓ Número encontrado en campo validación: {numero}")
                                resultado = f"ACTIVA - {numero}"
                                break
                    except:
                        pass
                    
                    if (intento + 1) % 5 == 0:
                        print(f"[DEBUG] Intento {intento+1}/{max_intentos}...")
                        
                except Exception as e:
                    print(f"[DEBUG] Error: {e}")
                    continue
            
            if resultado:
                if esperado in resultado:
                    print(f"\n✅ RESULTADO: {resultado} - CORRECTO")
                else:
                    print(f"\n⚠️  RESULTADO: {resultado} - ESPERADO: {esperado}")
            else:
                print(f"\n❌ RESULTADO: ERROR - No se detectó")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("PRUEBAS FINALES CON CÓDIGO CORREGIDO")
    print("="*60)
    
    # INACTIVAS
    test_iccid("0063704016891", "INACTIVA #1", "INACTIVA")
    test_iccid("0063704016909", "INACTIVA #2", "INACTIVA")
    
    # ACTIVAS
    test_iccid("0063491609627", "ACTIVA #1", "2281115989")
    test_iccid("0063251917780", "ACTIVA #2", "ACTIVA")
    
    print("\n" + "="*60)
    print("PRUEBAS COMPLETADAS")
    print("="*60 + "\n")
