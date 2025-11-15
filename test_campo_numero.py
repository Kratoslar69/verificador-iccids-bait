"""
Prueba para detectar el campo del número que aparece debajo del ICCID
"""

import time
import re
from playwright.sync_api import sync_playwright

iccid = "0063491609627"
url = "https://mibait.com/haz-tu-portabilidad"

print(f"\n{'='*60}")
print(f"PRUEBA: Detectar campo de número debajo del ICCID")
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
        
        # Llenar campo ICCID
        input_iccid = page.locator('input[placeholder*="13 dígitos"]').first
        input_iccid.click()
        time.sleep(0.3)
        input_iccid.fill(iccid)
        time.sleep(0.5)
        input_iccid.press("Enter")
        
        # Esperar 5 segundos
        print("[DEBUG] Esperando 5 segundos...")
        time.sleep(5)
        
        print("\n[DEBUG] Buscando elementos después del campo ICCID...\n")
        
        # MÉTODO 1: Buscar todos los inputs visibles
        print("1. Buscando todos los inputs visibles:")
        all_inputs = page.locator('input').all()
        for i, inp in enumerate(all_inputs):
            try:
                if inp.is_visible():
                    value = inp.input_value()
                    placeholder = inp.get_attribute('placeholder')
                    if value and len(value) == 10 and value.isdigit():
                        print(f"   ✓ Input {i}: value='{value}', placeholder='{placeholder}'")
            except:
                pass
        
        # MÉTODO 2: Buscar divs con texto numérico
        print("\n2. Buscando divs con números de 10 dígitos:")
        all_divs = page.locator('div').all()
        for i, div in enumerate(all_divs[:50]):  # Solo primeros 50
            try:
                text = div.inner_text()
                if text and len(text) == 10 and text.isdigit():
                    print(f"   ✓ Div {i}: text='{text}'")
            except:
                pass
        
        # MÉTODO 3: Buscar usando el texto visible completo
        print("\n3. Buscando en texto visible de la página:")
        page_text = page.evaluate("() => document.body.innerText")
        numeros = re.findall(r'\b[0-9]{10}\b', page_text)
        numeros_unicos = list(set(numeros))
        print(f"   Números únicos encontrados: {numeros_unicos}")
        
        # MÉTODO 4: Buscar elementos que contengan el número esperado
        print("\n4. Buscando elemento que contenga '2281115989':")
        try:
            elemento = page.locator('text=2281115989').first
            if elemento.is_visible(timeout=1000):
                print(f"   ✓ Elemento encontrado y visible!")
                print(f"   Tag: {elemento.evaluate('el => el.tagName')}")
                print(f"   Clase: {elemento.get_attribute('class')}")
        except Exception as e:
            print(f"   ✗ No encontrado: {e}")
        
        # MÉTODO 5: Screenshot para debugging
        print("\n5. Tomando screenshot...")
        page.screenshot(path='/home/ubuntu/screenshot_activa.png')
        print(f"   Screenshot guardado en: /home/ubuntu/screenshot_activa.png")
        
        # Verificar popup inactiva
        tiene_whatsapp = "btz.mx/whatsappbait" in page_text
        tiene_necesita = "necesita activarse" in page_text
        
        if tiene_whatsapp or tiene_necesita:
            print(f"\n⚠️  POPUP INACTIVA detectado (inesperado)")
        elif "2281115989" in page_text:
            print(f"\n✅ NÚMERO ENCONTRADO en texto visible")
        else:
            print(f"\n❌ Número NO encontrado")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.close()
