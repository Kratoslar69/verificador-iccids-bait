"""
Prueba específica para ACTIVA #1 que falló
"""

import time
import re
from playwright.sync_api import sync_playwright

iccid = "0063491609627"
url = "https://mibait.com/haz-tu-portabilidad"

print(f"\n{'='*60}")
print(f"PRUEBA ESPECÍFICA: ACTIVA #1")
print(f"ICCID: {iccid}")
print(f"Número esperado: 2281115989")
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
        
        # Verificar en múltiples intentos
        for intento in range(15):  # 15 intentos = 7.5 segundos adicionales
            time.sleep(0.5)
            
            page_html = page.content()
            
            # Verificar INACTIVA primero
            tiene_whatsapp = "btz.mx/whatsappbait" in page_html
            tiene_necesita = "necesita activarse" in page_html
            
            if tiene_whatsapp or tiene_necesita:
                print(f"\n[{intento+1}] ⚠️  POPUP INACTIVA detectado (inesperado)")
                break
            
            # Buscar TODOS los números de 10 dígitos
            numeros_encontrados = re.findall(r'\b[0-9]{10}\b', page_html)
            
            print(f"[{intento+1}] Números encontrados: {numeros_encontrados[:10]}")  # Primeros 10
            
            # Verificar si está el número esperado
            if "2281115989" in numeros_encontrados:
                print(f"\n✅ NÚMERO ESPERADO ENCONTRADO: 2281115989")
                break
            
            # Filtrar números válidos
            numeros_validos = [
                n for n in numeros_encontrados 
                if not n.startswith('895214')
                and n != iccid[:10]
                and not n.startswith('800')
                and not n.startswith('176310')
            ]
            
            if numeros_validos:
                print(f"   → Números válidos después de filtrar: {numeros_validos}")
                print(f"\n✅ NÚMERO DETECTADO: {numeros_validos[0]}")
                break
        else:
            print(f"\n❌ NO SE DETECTÓ NÚMERO después de 15 intentos")
            
            # Guardar HTML para análisis
            with open('/home/ubuntu/activa1_debug.html', 'w', encoding='utf-8') as f:
                f.write(page_html)
            print(f"📄 HTML guardado en: /home/ubuntu/activa1_debug.html")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    finally:
        browser.close()
