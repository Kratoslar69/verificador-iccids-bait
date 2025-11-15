"""
Script de prueba para depurar la detección de popups INACTIVA vs ACTIVA
"""

import time
import re
from playwright.sync_api import sync_playwright

def test_iccid_inactiva():
    """Probar con una ICCID conocida como INACTIVA"""
    
    iccid_test = "0063704016891"  # Conocida como INACTIVA
    url = "https://mibait.com/haz-tu-portabilidad"
    
    print(f"\n{'='*60}")
    print(f"PRUEBA: ICCID INACTIVA")
    print(f"ICCID: {iccid_test}")
    print(f"{'='*60}\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Visible para debugging
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        page = context.new_page()
        
        try:
            # Navegar
            print("1. Navegando al portal...")
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
            
            # Localizar campo
            print("2. Localizando campo de ICCID...")
            input_iccid = page.locator('input[placeholder*="13 dígitos"]').first
            
            if not input_iccid.is_visible(timeout=5000):
                print("❌ ERROR: Campo no encontrado")
                return
            
            # Llenar campo
            print(f"3. Llenando campo con: {iccid_test}")
            input_iccid.click()
            time.sleep(0.3)
            input_iccid.fill(iccid_test)
            time.sleep(0.5)
            
            # Presionar Enter
            print("4. Presionando Enter...")
            input_iccid.press("Enter")
            
            # Esperar y detectar popup
            print("5. Esperando popup (máximo 10 segundos)...\n")
            
            max_intentos = 20
            popup_detectado = False
            
            for intento in range(max_intentos):
                time.sleep(0.5)
                
                try:
                    page_html = page.content()
                    
                    # Verificar elementos específicos
                    tiene_whatsapp = "btz.mx/whatsappbait" in page_html
                    tiene_aceptar = "Aceptar" in page_html
                    tiene_necesita = "necesita activarse" in page_html
                    tiene_validacion = "Validación automática" in page_html
                    
                    print(f"   Intento {intento+1:2d}: whatsapp={tiene_whatsapp}, aceptar={tiene_aceptar}, necesita={tiene_necesita}, validacion={tiene_validacion}")
                    
                    # Detectar INACTIVA
                    if tiene_whatsapp or (tiene_aceptar and tiene_necesita):
                        print(f"\n✅ POPUP INACTIVA DETECTADO en intento {intento+1}")
                        print(f"   - Enlace whatsapp: {tiene_whatsapp}")
                        print(f"   - Botón Aceptar: {tiene_aceptar}")
                        print(f"   - Texto 'necesita activarse': {tiene_necesita}")
                        popup_detectado = True
                        
                        # Guardar HTML para análisis
                        with open('/home/ubuntu/popup_inactiva.html', 'w', encoding='utf-8') as f:
                            f.write(page_html)
                        print(f"\n📄 HTML guardado en: /home/ubuntu/popup_inactiva.html")
                        break
                    
                    # Detectar ACTIVA
                    if tiene_validacion:
                        print(f"\n⚠️  VALIDACIÓN AUTOMÁTICA DETECTADA en intento {intento+1}")
                        print(f"   ¡ESTO ES INCORRECTO! Esta ICCID debería ser INACTIVA")
                        numeros = re.findall(r'\b[0-9]{10}\b', page_html)
                        print(f"   Números encontrados: {numeros}")
                        popup_detectado = True
                        
                        # Guardar HTML para análisis
                        with open('/home/ubuntu/popup_error.html', 'w', encoding='utf-8') as f:
                            f.write(page_html)
                        print(f"\n📄 HTML guardado en: /home/ubuntu/popup_error.html")
                        break
                        
                except Exception as e:
                    print(f"   ❌ Error en intento {intento+1}: {e}")
                    continue
            
            if not popup_detectado:
                print(f"\n❌ NO SE DETECTÓ POPUP después de {max_intentos} intentos")
                # Guardar HTML final
                with open('/home/ubuntu/popup_timeout.html', 'w', encoding='utf-8') as f:
                    f.write(page.content())
                print(f"📄 HTML guardado en: /home/ubuntu/popup_timeout.html")
            
            # Esperar para ver el resultado
            print("\n⏸️  Esperando 5 segundos para inspección visual...")
            time.sleep(5)
            
        except Exception as e:
            print(f"\n❌ ERROR GENERAL: {e}")
        finally:
            browser.close()
            print("\n✅ Navegador cerrado")

if __name__ == "__main__":
    test_iccid_inactiva()
