"""
Prueba final con el código corregido
"""

import time
import re
from playwright.sync_api import sync_playwright

def test_iccid(iccid_13_digitos, nombre):
    """Probar una ICCID con el código corregido"""
    
    url = "https://mibait.com/haz-tu-portabilidad"
    
    print(f"\n{'='*60}")
    print(f"PRUEBA: {nombre}")
    print(f"ICCID: {iccid_13_digitos}")
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
            
            # ESPERA FIJA DE 5 SEGUNDOS (código corregido)
            print("[DEBUG] Esperando 5 segundos...")
            time.sleep(5)
            
            # Verificar contenido
            max_intentos = 10
            popup_detectado = False
            
            for intento in range(max_intentos):
                time.sleep(0.5)
                
                try:
                    page_text = page.content()
                    
                    # CASO 1: INACTIVA (buscar primero)
                    tiene_whatsapp = "btz.mx/whatsappbait" in page_text
                    tiene_necesita = "necesita activarse" in page_text
                    
                    if tiene_whatsapp or tiene_necesita:
                        print(f"[DEBUG] ✓ Popup de INACTIVA detectado en intento {intento+1}")
                        print(f"[DEBUG]   - whatsapp: {tiene_whatsapp}, necesita: {tiene_necesita}")
                        print(f"\n✅ RESULTADO: INACTIVA")
                        popup_detectado = True
                        break
                    
                    # CASO 2: ACTIVA (buscar número telefónico)
                    numeros_encontrados = re.findall(r'\b[0-9]{10}\b', page_text)
                    numeros_validos = [
                        n for n in numeros_encontrados 
                        if not n.startswith('895214')
                        and n != iccid_13_digitos[:10]
                        and not n.startswith('800')
                        and not n.startswith('176310')
                    ]
                    
                    if numeros_validos:
                        numero = numeros_validos[0]
                        print(f"[DEBUG] ✓ Número telefónico encontrado: {numero}")
                        print(f"\n✅ RESULTADO: ACTIVA - Número: {numero}")
                        popup_detectado = True
                        break
                    
                    if (intento + 1) % 5 == 0:
                        print(f"[DEBUG] Intento {intento+1}/{max_intentos}...")
                        
                except Exception as e:
                    print(f"[DEBUG] Error: {e}")
                    continue
            
            if not popup_detectado:
                print(f"\n⚠️  RESULTADO: ERROR - No se detectó popup")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    # Probar con ICCIDs conocidas
    print("\n" + "="*60)
    print("PRUEBAS CON CÓDIGO CORREGIDO")
    print("="*60)
    
    # INACTIVAS conocidas
    test_iccid("0063704016891", "INACTIVA #1")
    test_iccid("0063704016909", "INACTIVA #2")
    
    # ACTIVAS conocidas
    test_iccid("0063491609627", "ACTIVA #1")
    test_iccid("0063251917780", "ACTIVA #2")
    
    print("\n" + "="*60)
    print("PRUEBAS COMPLETADAS")
    print("="*60 + "\n")
