"""
Prueba con blur (Tab) en lugar de Enter
"""

import time
import re
from playwright.sync_api import sync_playwright

iccid = "0063491609627"
url = "https://mibait.com/haz-tu-portabilidad"

print(f"\n{'='*60}")
print(f"PRUEBA V3: Usar blur (Tab) en lugar de Enter")
print(f"ICCID: {iccid}")
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
        input_iccid.fill(iccid)
        time.sleep(0.5)
        
        # Probar con Tab (blur) en lugar de Enter
        print("[DEBUG] Presionando Tab para hacer blur...")
        input_iccid.press("Tab")
        
        # Esperar 8 segundos (más tiempo)
        print("[DEBUG] Esperando 8 segundos...")
        time.sleep(8)
        
        # Verificar texto visible
        page_text = page.evaluate("() => document.body.innerText")
        
        # Buscar números
        numeros = re.findall(r'\b[0-9]{10}\b', page_text)
        print(f"\n[DEBUG] Números encontrados: {numeros}")
        
        # Verificar popup inactiva
        tiene_whatsapp = "btz.mx/whatsappbait" in page_text
        tiene_necesita = "necesita activarse" in page_text
        
        if tiene_whatsapp or tiene_necesita:
            print(f"\n⚠️  POPUP DE INACTIVA detectado")
            print(f"   - whatsapp: {tiene_whatsapp}")
            print(f"   - necesita: {tiene_necesita}")
        elif "2281115989" in numeros:
            print(f"\n✅ NÚMERO ESPERADO ENCONTRADO: 2281115989")
        elif numeros:
            numeros_validos = [
                n for n in numeros 
                if not n.startswith('895214')
                and not n.startswith('800')
                and not n.startswith('176310')
            ]
            if numeros_validos:
                print(f"\n✅ NÚMERO DETECTADO: {numeros_validos[0]}")
            else:
                print(f"\n❌ Solo números no válidos encontrados")
        else:
            print(f"\n❌ NO se detectó número ni popup")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    finally:
        browser.close()
