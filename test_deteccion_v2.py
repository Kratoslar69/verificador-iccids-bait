"""
Script de prueba V2 - Esperar más tiempo para el popup
"""

import time
from playwright.sync_api import sync_playwright

def test_iccid_inactiva_v2():
    """Probar con espera más larga"""
    
    iccid_test = "0063704016891"  # Conocida como INACTIVA
    url = "https://mibait.com/haz-tu-portabilidad"
    
    print(f"\n{'='*60}")
    print(f"PRUEBA V2: ICCID INACTIVA (espera extendida)")
    print(f"ICCID: {iccid_test}")
    print(f"{'='*60}\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        
        try:
            # Navegar
            print("1. Navegando...")
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
            
            # Llenar campo
            print("2. Llenando campo...")
            input_iccid = page.locator('input[placeholder*="13 dígitos"]').first
            input_iccid.click()
            time.sleep(0.3)
            input_iccid.fill(iccid_test)
            time.sleep(0.5)
            input_iccid.press("Enter")
            
            print("3. Esperando popup...\n")
            
            # Esperar 5 segundos completos antes de verificar
            for i in range(10):
                time.sleep(0.5)
                print(f"   {i+1}/10 segundos...")
            
            print("\n4. Verificando contenido...")
            page_html = page.content()
            
            # Verificar elementos
            tiene_whatsapp = "btz.mx/whatsappbait" in page_html
            tiene_aceptar = "Aceptar" in page_html
            tiene_necesita = "necesita activarse" in page_html
            tiene_validacion = "Validación automática" in page_html
            
            print(f"\n   Resultados:")
            print(f"   - whatsapp link: {tiene_whatsapp}")
            print(f"   - botón Aceptar: {tiene_aceptar}")
            print(f"   - texto 'necesita activarse': {tiene_necesita}")
            print(f"   - texto 'Validación automática': {tiene_validacion}")
            
            # Guardar HTML
            with open('/home/ubuntu/popup_5seg.html', 'w', encoding='utf-8') as f:
                f.write(page_html)
            print(f"\n📄 HTML guardado en: /home/ubuntu/popup_5seg.html")
            
            # Decisión
            if tiene_whatsapp or (tiene_aceptar and tiene_necesita):
                print(f"\n✅ CORRECTO: ICCID INACTIVA detectada")
            elif tiene_validacion:
                print(f"\n❌ ERROR: Se detectó 'Validación automática' (falso positivo)")
            else:
                print(f"\n⚠️  TIMEOUT: No se detectó ningún popup")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_iccid_inactiva_v2()
