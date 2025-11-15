"""
Prueba con búsqueda de elementos visibles en el DOM
"""

import time
from playwright.sync_api import sync_playwright

iccid = "0063491609627"
url = "https://mibait.com/haz-tu-portabilidad"

print(f"\n{'='*60}")
print(f"PRUEBA V2: Buscar número en elementos visibles")
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
        input_iccid.press("Enter")
        
        # Esperar 5 segundos
        print("[DEBUG] Esperando 5 segundos...")
        time.sleep(5)
        
        # Buscar el texto visible en la página
        print("\n[DEBUG] Buscando texto visible en la página...")
        page_text = page.evaluate("() => document.body.innerText")
        
        print(f"\n[DEBUG] Texto visible (primeros 2000 caracteres):")
        print(page_text[:2000])
        
        # Buscar números de 10 dígitos en el texto visible
        import re
        numeros = re.findall(r'\b[0-9]{10}\b', page_text)
        print(f"\n[DEBUG] Números de 10 dígitos encontrados: {numeros}")
        
        # Verificar si está el número esperado
        if "2281115989" in page_text:
            print(f"\n✅ NÚMERO ESPERADO ENCONTRADO en texto visible")
        else:
            print(f"\n❌ Número esperado NO encontrado en texto visible")
        
        # Buscar popup de inactiva
        if "btz.mx/whatsappbait" in page_text or "necesita activarse" in page_text:
            print(f"\n⚠️  POPUP DE INACTIVA detectado")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    finally:
        browser.close()
